#!/usr/bin/env python3
"""
XML Parser for std.xsd schema using xsdata generated models.

This parser uses the automatically generated dataclasses from xsdata
to parse XML files conforming to the std.xsd schema.
"""

import xml.etree.ElementTree as ET
from typing import Optional
from simbat_models.std import Site, Composition, Side, XyGps, Glazing


class XSDataStdParser:
    """Parser for std.xsd schema using xsdata generated models."""
    
    def __init__(self):
        self.namespace = {"std": "http://simbat.fr/std"}
    
    def parse_file(self, file_path: str) -> Site:
        """Parse an XML file conforming to the std.xsd schema."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check if root is the site element or find it
            if root.tag.endswith('site'):
                site_elem = root
            else:
                site_elem = root.find('std:site', self.namespace)
                if site_elem is None:
                    raise ValueError("XML file must contain a site element")
            
            return self.parse_site(site_elem)
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing XML file: {e}")
    
    def parse_string(self, xml_string: str) -> Site:
        """Parse an XML string conforming to the std.xsd schema."""
        try:
            root = ET.fromstring(xml_string)
            
            # Check if root is the site element or find it
            if root.tag.endswith('site'):
                site_elem = root
            else:
                site_elem = root.find('std:site', self.namespace)
                if site_elem is None:
                    raise ValueError("XML string must contain a site element")
            
            return self.parse_site(site_elem)
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML string: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing XML string: {e}")
    
    def parse_site(self, element: ET.Element) -> Site:
        """Parse Site element using xsdata model."""
        from xsdata.formats.dataclass.parsers import XmlParser
        from xsdata.formats.dataclass.parsers.config import ParserConfig
        
        # Create XML string from element
        xml_string = ET.tostring(element, encoding='unicode')
        
        # Parse using xsdata
        parser = XmlParser(config=ParserConfig(fail_on_unknown_properties=False))
        return parser.from_string(xml_string, Site)
    
    def get_composition_by_id(self, site: Site, composition_id: str) -> Optional[Composition]:
        """Get a composition by its ID."""
        if site.compositions and site.compositions.composition:
            for comp in site.compositions.composition:
                if comp.composition_id == composition_id:
                    return comp
        return None
    
    def get_glazing_by_id(self, site: Site, glazing_id: str) -> Optional[Glazing]:
        """Get a glazing definition by its ID."""
        # Note: The current schema doesn't show where glazing definitions are stored
        # This would need to be implemented based on the actual schema structure
        return None
    
    def get_xy_gps_by_id(self, site: Site, gps_id: str) -> Optional[XyGps]:
        """Get a GPS point by its ID."""
        if site.coordinates and site.coordinates.xy_gps:
            for gps in site.coordinates.xy_gps:
                if gps.id == gps_id:
                    return gps
        return None
    
    def get_roof_composition(self, site: Site) -> Optional[Composition]:
        """Get the roof composition from the site."""
        if site.roof_composition:
            return self.get_composition_by_id(site, site.roof_composition)
        return None
    
    def get_ground_composition(self, site: Site) -> Optional[Composition]:
        """Get the ground composition from the site."""
        if site.ground_composition:
            return self.get_composition_by_id(site, site.ground_composition)
        return None
    
    def get_floor_composition(self, site: Site) -> Optional[Composition]:
        """Get the floor composition from the site."""
        if site.floor_composition:
            return self.get_composition_by_id(site, site.floor_composition)
        return None
    
    def get_composition_for_side(self, site: Site, side: Side) -> Optional[Composition]:
        """Get the plain composition for a side."""
        if side.composition_id:
            return self.get_composition_by_id(site, side.composition_id)
        return None
    
    def get_glazing_composition_for_side(self, site: Site, side: Side) -> Optional[Composition]:
        """Get the glazing composition for a side."""
        if side.glazing:
            # This would need to be implemented based on how glazing is structured
            # in the actual schema
            return None
        return None


if __name__ == "__main__":
    parser = XSDataStdParser()
    try:
        site = parser.parse_file("simbat/std_ensag.xml")
        print("✅ Successfully parsed site:", site.name)
        print(f"   Location: {site.latitude}°E, {site.longitude}°N")
        print(f"   Height: {site.height}m, Floors: {site.n_floors}")
        
        if site.coordinates:
            print(f"   GPS points: {len(site.coordinates.xy_gps)}")
        if site.sides:
            print(f"   Sides: {len(site.sides.side)}")
        if site.compositions:
            print(f"   Compositions: {len(site.compositions.composition)}")
        if site.perimeter:
            print(f"   Perimeter: {len(site.perimeter.xy_gps_id)} points")
        
        # Show first side details
        if site.sides and site.sides.side:
            first_side = site.sides.side[0]
            print(f"\nFirst side: {first_side.xy_id}")
            
            # Get plain composition
            plain_comp = parser.get_composition_for_side(site, first_side)
            if plain_comp:
                print(f"  Plain composition ({plain_comp.composition_id}): {len(plain_comp.layer)} layers")
                for layer in plain_comp.layer:
                    print(f"    - {layer.material}: {layer.thickness}m")
        
        # Show main compositions
        print("\nMain Compositions:")
        
        roof_comp = parser.get_roof_composition(site)
        if roof_comp:
            print(f"  Roof ({roof_comp.composition_id}): {len(roof_comp.layer)} layers")
            for layer in roof_comp.layer:
                print(f"    - {layer.material}: {layer.thickness}m")
        
        ground_comp = parser.get_ground_composition(site)
        if ground_comp:
            print(f"  Ground ({ground_comp.composition_id}): {len(ground_comp.layer)} layers")
            for layer in ground_comp.layer:
                print(f"    - {layer.material}: {layer.thickness}m")
        
        floor_comp = parser.get_floor_composition(site)
        if floor_comp:
            print(f"  Floor ({floor_comp.composition_id}): {len(floor_comp.layer)} layers")
            for layer in floor_comp.layer:
                print(f"    - {layer.material}: {layer.thickness}m")
        
        # Show all compositions
        if site.compositions:
            print("\nAll Compositions:")
            for comp in site.compositions.composition:
                print(f"  {comp.composition_id}: {len(comp.layer)} layers")
                for layer in comp.layer:
                    print(f"    - {layer.material}: {layer.thickness}m")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
