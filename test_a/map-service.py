"""
map_service.py - Map service for displaying events on OpenStreetMap
"""
import folium
from folium import plugins
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MapService:
    """Service for creating interactive maps with event locations"""
    
    def __init__(self, config):
        self.config = config
        
        # Map styling options
        self.tile_options = {
            'default': 'OpenStreetMap',
            'dark': 'CartoDB dark_matter',
            'light': 'CartoDB positron',
            'satellite': 'Esri WorldImagery'
        }
        
        # Icon colors for different event categories
        self.category_colors = {
            'music': 'purple',
            'arts': 'pink',
            'food': 'orange',
            'sports': 'green',
            'technology': 'blue',
            'business': 'gray',
            'education': 'darkblue',
            'health': 'lightgreen',
            'community': 'red',
            'entertainment': 'lightred',
            'default': 'blue'
        }
        
        # Icon types for different event categories
        self.category_icons = {
            'music': 'music',
            'arts': 'palette',
            'food': 'utensils',
            'sports': 'running',
            'technology': 'laptop',
            'business': 'briefcase',
            'education': 'graduation-cap',
            'health': 'heartbeat',
            'community': 'users',
            'entertainment': 'film',
            'default': 'calendar'
        }
    
    def create_event_map(self, 
                        events: List[Dict],
                        user_location: Tuple[float, float],
                        radius_miles: int = 50,
                        map_style: str = 'default') -> str:
        """
        Create an interactive map with event markers
        
        Args:
            events: List of event dictionaries
            user_location: User's (latitude, longitude)
            radius_miles: Search radius to display
            map_style: Map tile style
            
        Returns:
            HTML string of the map
        """
        # Create base map centered on user location
        m = folium.Map(
            location=user_location,
            zoom_start=11,
            tiles=self.tile_options.get(map_style, 'OpenStreetMap'),
            prefer_canvas=True
        )
        
        # Add user location marker
        self._add_user_marker(m, user_location)
        
        # Add search radius circle
        self._add_radius_circle(m, user_location, radius_miles)
        
        # Add event markers
        event_group = folium.FeatureGroup(name='Events')
        for event in events:
            self._add_event_marker(event_group, event, user_location)
        event_group.add_to(m)
        
        # Add marker clustering for better performance with many events
        marker_cluster = plugins.MarkerCluster(
            name='Event Clusters',
            overlay=True,
            control=True,
            icon_create_function=self._get_cluster_icon_function()
        )
        
        # Add clustered markers
        for event in events:
            if event.get('coordinates'):
                self._add_clustered_marker(marker_cluster, event)
        
        marker_cluster.add_to(m)
        
        # Add map controls
        self._add_map_controls(m)
        
        # Generate and return HTML
        return m._repr_html_()
    
    def create_heatmap(self, 
                      events: List[Dict],
                      user_location: Tuple[float, float]) -> str:
        """
        Create a heatmap of event density
        
        Args:
            events: List of event dictionaries
            user_location: User's (latitude, longitude)
            
        Returns:
            HTML string of the heatmap
        """
        # Create base map
        m = folium.Map(
            location=user_location,
            zoom_start=11,
            tiles='CartoDB positron'
        )
        
        # Prepare heatmap data
        heat_data = []
        for event in events:
            if event.get('coordinates'):
                lat = event['coordinates']['lat']
                lng = event['coordinates']['lng']
                # Weight by relevance score if available
                weight = event.get('relevance_score', 0.5)
                heat_data.append([lat, lng, weight])
        
        # Add heatmap layer
        if heat_data:
            plugins.HeatMap(
                heat_data,
                name='Event Density',
                min_opacity=0.2,
                max_zoom=18,
                radius=15,
                blur=15,
                gradient={
                    0.0: 'blue',
                    0.5: 'cyan',
                    0.7: 'lime',
                    0.9: 'yellow',
                    1.0: 'red'
                }
            ).add_to(m)
        
        # Add user location
        self._add_user_marker(m, user_location)
        
        # Add controls
        folium.LayerControl().add_to(m)
        
        return m._repr_html_()
    
    def _add_user_marker(self, map_obj: folium.Map, location: Tuple[float, float]):
        """Add user location marker"""
        folium.Marker(
            location,
            popup=folium.Popup('Your Location', max_width=200),
            tooltip='You are here',
            icon=folium.Icon(
                color='red',
                icon='user',
                prefix='fa'
            )
        ).add_to(map_obj)
        
        # Add pulsing effect to user location
        folium.CircleMarker(
            location,
            radius=8,
            popup='Your Location',
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.4,
            weight=2
        ).add_to(map_obj)
    
    def _add_radius_circle(self, map_obj: folium.Map, 
                          center: Tuple[float, float], 
                          radius_miles: int):
        """Add search radius circle"""
        # Convert miles to meters
        radius_meters = radius_miles * 1609.34
        
        folium.Circle(
            center,
            radius=radius_meters,
            popup=f'{radius_miles} mile radius',
            color='blue',
            fill=True,
            fillColor='blue',
            fillOpacity=0.1,
            weight=2,
            dashArray='5, 5'
        ).add_to(map_obj)
    
    def _add_event_marker(self, feature_group: folium.FeatureGroup, 
                         event: Dict, 
                         user_location: Tuple[float, float]):
        """Add individual event marker"""
        if not event.get('coordinates'):
            return
        
        lat = event['coordinates']['lat']
        lng = event['coordinates']['lng']
        
        # Get category-specific styling
        category = event.get('category', 'default').lower()
        color = self.category_colors.get(category, self.category_colors['default'])
        icon = self.category_icons.get(category, self.category_icons['default'])
        
        # Create popup content
        popup_html = self._create_popup_html(event)
        
        # Create marker
        marker = folium.Marker(
            [lat, lng],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{event['name']} - {event.get('time', 'Time TBD')}",
            icon=folium.Icon(
                color=color,
                icon=icon,
                prefix='fa'
            )
        )
        
        marker.add_to(feature_group)
    
    def _add_clustered_marker(self, cluster: plugins.MarkerCluster, event: Dict):
        """Add marker to cluster"""
        if not event.get('coordinates'):
            return
        
        lat = event['coordinates']['lat']
        lng = event['coordinates']['lng']
        
        # Simple popup for clustered markers
        popup_text = f"{event['name']}<br>{event.get('venue', 'Venue TBD')}"
        
        folium.Marker(
            [lat, lng],
            popup=popup_text,
            tooltip=event['name']
        ).add_to(cluster)
    
    def _create_popup_html(self, event: Dict) -> str:
        """Create HTML content for event popup"""
        # Format matching interests
        interests_html = ''
        if event.get('matching_interests'):
            interests = ', '.join(event['matching_interests'][:3])
            if len(event['matching_interests']) > 3:
                interests += '...'
            interests_html = f'<br><small><i>Matches: {interests}</i></small>'
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 300px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">{event['name']}</h4>
            <p style="margin: 5px 0;">
                <i class="fa fa-clock"></i> {event.get('date', 'Date TBD')} at {event.get('time', 'Time TBD')}<br>
                <i class="fa fa-hourglass-half"></i> Starts in {event.get('time_until', 'N/A')}<br>
                <i class="fa fa-map-marker"></i> {event.get('venue', 'Venue TBD')}<br>
                <i class="fa fa-road"></i> {event.get('distance', 'Distance N/A')}<br>
                <i class="fa fa-tag"></i> {event.get('category', 'General')}<br>
                <i class="fa fa-star"></i> Relevance: {event.get('relevance', 'N/A')}
                {interests_html}
            </p>
            <div style="margin-top: 10px;">
                <a href="{event.get('url', '#')}" target="_blank" 
                   style="background-color: #f6682d; color: white; padding: 8px 16px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    View Event
                </a>
            </div>
        </div>
        """
        return html
    
    def _get_cluster_icon_function(self) -> str:
        """Get JavaScript function for cluster icons"""
        return """
        function(cluster) {
            var childCount = cluster.getChildCount();
            var c = ' marker-cluster-';
            if (childCount < 10) {
                c += 'small';
            } else if (childCount < 50) {
                c += 'medium';
            } else {
                c += 'large';
            }
            return new L.DivIcon({
                html: '<div><span>' + childCount + '</span></div>',
                className: 'marker-cluster' + c,
                iconSize: new L.Point(40, 40)
            });
        }
        """
    
    def _add_map_controls(self, map_obj: folium.Map):
        """Add various map controls"""
        # Add fullscreen button
        plugins.Fullscreen(
            position='topright',
            title='Fullscreen',
            title_cancel='Exit Fullscreen',
            force_separate_button=True
        ).add_to(map_obj)
        
        # Add location search
        plugins.Geocoder(
            collapsed=True,
            position='topleft'
        ).add_to(map_obj)
        
        # Add measure control
        plugins.MeasureControl(
            position='topleft',
            primary_length_unit='miles',
            secondary_length_unit='kilometers',
            primary_area_unit='sqmiles',
            secondary_area_unit='sqmeters'
        ).add_to(map_obj)
        
        # Add layer control
        folium.LayerControl(position='topright').add_to(map_obj)
    
    def create_event_timeline(self, events: List[Dict]) -> str:
        """Create a timeline visualization of events"""
        timeline_data = []
        
        for event in events:
            if event.get('coordinates') and event.get('start_time'):
                timeline_data.append({
                    'name': event['name'],
                    'coordinates': [event['coordinates']['lat'], event['coordinates']['lng']],
                    'time': event['start_time'],
                    'popup': self._create_popup_html(event)
                })
        
        # Sort by time
        timeline_data.sort(key=lambda x: x['time'])
        
        # Create timeline map
        m = folium.Map(
            location=events[0]['coordinates'] if events else [0, 0],
            zoom_start=11
        )
        
        # Add timeline plugin
        features = []
        for item in timeline_data:
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [item['coordinates'][1], item['coordinates'][0]]
                },
                'properties': {
                    'time': item['time'],
                    'popup': item['popup'],
                    'icon': 'circle',
                    'iconstyle': {
                        'fillColor': '#f6682d',
                        'fillOpacity': 0.8,
                        'stroke': True,
                        'radius': 8
                    }
                }
            })
        
        # Add timeline
        plugins.TimestampedGeoJson(
            {
                'type': 'FeatureCollection',
                'features': features
            },
            period='PT1M',
            add_last_point=True,
            loop=False
        ).add_to(m)
        
        return m._repr_html_()
    
    def export_map_data(self, events: List[Dict], format: str = 'geojson') -> str:
        """Export event data in various formats"""
        if format == 'geojson':
            features = []
            for event in events:
                if event.get('coordinates'):
                    features.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [
                                event['coordinates']['lng'],
                                event['coordinates']['lat']
                            ]
                        },
                        'properties': {
                            'name': event['name'],
                            'venue': event.get('venue', ''),
                            'time': event.get('time', ''),
                            'category': event.get('category', ''),
                            'url': event.get('url', '')
                        }
                    })
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }
            
            return json.dumps(geojson, indent=2)
        
        elif format == 'kml':
            # Simple KML export
            kml = ['<?xml version="1.0" encoding="UTF-8"?>']
            kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
            kml.append('<Document>')
            kml.append('<name>EventBrite Events</name>')
            
            for event in events:
                if event.get('coordinates'):
                    kml.append('<Placemark>')
                    kml.append(f'<name>{event["name"]}</name>')
                    kml.append(f'<description>{event.get("venue", "")} - {event.get("time", "")}</description>')
                    kml.append('<Point>')
                    kml.append(f'<coordinates>{event["coordinates"]["lng"]},{event["coordinates"]["lat"]},0</coordinates>')
                    kml.append('</Point>')
                    kml.append('</Placemark>')
            
            kml.append('</Document>')
            kml.append('</kml>')
            
            return '\n'.join(kml)
        
        return ""
