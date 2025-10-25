#!/usr/bin/env python3
"""
XML Parser for std.xsd schema using xsdata generated models.

This parser uses the automatically generated dataclasses from xsdata
to parse XML files conforming to the std.xsd schema.
"""

import xml.etree.ElementTree as ET
from typing import Optional
from .data_models.std import (
    Site, Composition, Glazing, XyGps, Side, Mask, Layer,
    Coordinates, Perimeter, Sides, Compositions, Masks, Surrounding
)


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
        """Parse Site element using ElementTree and data models."""
        # Parse basic site attributes
        name = element.find('std:name', self.namespace).text
        latitude = float(element.find('std:latitude', self.namespace).text)
        longitude = float(element.find('std:longitude', self.namespace).text)
        height = float(element.find('std:height', self.namespace).text)
        n_floors = int(element.find('std:n_floors', self.namespace).text)

        # Parse compositions
        roof_composition = element.find('std:roof_composition', self.namespace).text
        ground_composition = element.find('std:ground_composition', self.namespace).text
        floor_composition_elem = element.find('std:floor_composition', self.namespace)
        floor_composition = floor_composition_elem.text if floor_composition_elem is not None else None

        # Parse perimeter
        perimeter_elem = element.find('std:perimeter', self.namespace)
        perimeter = self._parse_perimeter(perimeter_elem)

        # Parse sides
        sides_elem = element.find('std:sides', self.namespace)
        sides = self._parse_sides(sides_elem)

        # Parse coordinates
        coordinates_elem = element.find('std:coordinates', self.namespace)
        coordinates = self._parse_coordinates(coordinates_elem)

        # Parse compositions
        compositions_elem = element.find('std:compositions', self.namespace)
        compositions = self._parse_compositions(compositions_elem)

        # Parse optional elements
        surrounding_elem = element.find('std:surrounding', self.namespace)
        surrounding = self._parse_surrounding(surrounding_elem) if surrounding_elem is not None else None

        masks_elem = element.find('std:masks', self.namespace)
        masks = self._parse_masks(masks_elem) if masks_elem is not None else None

        return Site(
            name=name,
            latitude=latitude,
            longitude=longitude,
            height=height,
            n_floors=n_floors,
            roof_composition=roof_composition,
            ground_composition=ground_composition,
            floor_composition=floor_composition,
            perimeter=perimeter,
            sides=sides,
            surrounding=surrounding,
            coordinates=coordinates,
            compositions=compositions,
            masks=masks
        )

    def _parse_perimeter(self, element: ET.Element) -> Perimeter:
        """Parse Perimeter element."""
        # Defaults are 0 in XSD when missing
        offset_x_elem = element.find('std:offset_x', self.namespace)
        offset_y_elem = element.find('std:offset_y', self.namespace)
        offset_x = float(offset_x_elem.text) if offset_x_elem is not None else 0.0
        offset_y = float(offset_y_elem.text) if offset_y_elem is not None else 0.0
        xy_gps_id = [elem.text for elem in element.findall('std:xy_gps_id', self.namespace)]
        return Perimeter(offset_x=offset_x, offset_y=offset_y, xy_gps_id=xy_gps_id)

    def _parse_sides(self, element: ET.Element) -> Sides:
        """Parse Sides element."""
        sides = []
        for side_elem in element.findall('std:side', self.namespace):
            xy_id = [elem.text for elem in side_elem.findall('std:xy_id', self.namespace)]
            composition_id = side_elem.find('std:composition_id', self.namespace).text
            glazing_elem = side_elem.find('std:glazing', self.namespace)
            glazing = glazing_elem.text if glazing_elem is not None else None
            sides.append(Side(xy_id=xy_id, composition_id=composition_id, glazing=glazing))
        return Sides(side=sides)

    def _parse_coordinates(self, element: ET.Element) -> Coordinates:
        """Parse Coordinates element."""
        # Defaults are 0 in XSD when missing
        offset_x_elem = element.find('std:offset_x', self.namespace)
        offset_y_elem = element.find('std:offset_y', self.namespace)
        offset_x = float(offset_x_elem.text) if offset_x_elem is not None else 0.0
        offset_y = float(offset_y_elem.text) if offset_y_elem is not None else 0.0
        xy_gps_list = []
        for gps_elem in element.findall('std:xy_gps', self.namespace):
            gps_id = gps_elem.find('std:id', self.namespace).text
            x = float(gps_elem.find('std:x', self.namespace).text)
            y = float(gps_elem.find('std:y', self.namespace).text)
            xy_gps_list.append(XyGps(id=gps_id, x=x, y=y))
        return Coordinates(offset_x=offset_x, offset_y=offset_y, xy_gps=xy_gps_list)

    def _parse_compositions(self, element: ET.Element) -> Compositions:
        """Parse Compositions element."""
        compositions = []
        for comp_elem in element.findall('std:composition', self.namespace):
            composition_id = comp_elem.find('std:composition_id', self.namespace).text
            layers = []
            for layer_elem in comp_elem.findall('std:layer', self.namespace):
                material = layer_elem.find('std:material', self.namespace).text
                thickness = float(layer_elem.find('std:thickness', self.namespace).text)
                layers.append(Layer(material=material, thickness=thickness))
            compositions.append(Composition(composition_id=composition_id, layer=layers))
        return Compositions(composition=compositions)

    def _parse_surrounding(self, element: ET.Element) -> Surrounding:
        """Parse Surrounding element."""
        masks = []
        for mask_elem in element.findall('std:mask', self.namespace):
            mask = self._parse_mask(mask_elem)
            masks.append(mask)
        return Surrounding(mask=masks)

    def _parse_masks(self, element: ET.Element) -> Masks:
        """Parse Masks element."""
        masks = []
        for mask_elem in element.findall('std:mask', self.namespace):
            mask = self._parse_mask(mask_elem)
            masks.append(mask)
        return Masks(mask=masks)

    def _parse_mask(self, element: ET.Element) -> Mask:
        """Parse individual Mask element."""
        height = float(element.find('std:height', self.namespace).text)
        width = float(element.find('std:width', self.namespace).text)
        distance_to_ground_gravity_m = float(element.find('std:distance_to_ground_gravity_m', self.namespace).text)
        exposure = float(element.find('std:exposure', self.namespace).text)
        # Defaults per XSD: slope=90, rotation=0, elevation=0
        slope_elem = element.find('std:slope', self.namespace)
        rotation_elem = element.find('std:rotation', self.namespace)
        elevation_elem = element.find('std:elevation', self.namespace)
        slope = float(slope_elem.text) if slope_elem is not None else 90.0
        rotation = float(rotation_elem.text) if rotation_elem is not None else 0.0
        elevation = float(elevation_elem.text) if elevation_elem is not None else 0.0
        return Mask(
            height=height,
            width=width,
            distance_to_ground_gravity_m=distance_to_ground_gravity_m,
            exposure=exposure,
            slope=slope,
            rotation=rotation,
            elevation=elevation
        )

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
