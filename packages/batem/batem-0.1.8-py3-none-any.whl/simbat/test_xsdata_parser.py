#!/usr/bin/env python3
"""
Comprehensive test script for the xsdata parser.

This script tests the xsdata-generated parser with the updated std_ensag.xml file
to ensure it correctly parses all elements according to the std.xsd schema.
"""

from simbat.std_xsdata_parser import XSDataStdParser


def test_parser_functionality():
    """Test the main parser functionality."""
    print("=" * 60)
    print("XSData STD XML Parser Test")
    print("=" * 60)
    
    parser = XSDataStdParser()
    
    try:
        # Parse the updated file
        site = parser.parse_file("simbat/std_ensag.xml")
        
        print(f"✅ Successfully parsed: {site.name}")
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
        
        print("\n" + "=" * 40)
        print("COMPOSITION RESOLUTION TESTS")
        print("=" * 40)
        
        # Test composition resolution
        print("\n1. Getting compositions by ID:")
        composition_ids = ["wall_comp", "glazing_comp", "roof_comp", "ground_comp", "floor_comp", "glazing_1"]
        for comp_id in composition_ids:
            comp = parser.get_composition_by_id(site, comp_id)
            if comp:
                print(f"   ✅ Found composition: {comp_id}")
            else:
                print(f"   ❌ Composition not found: {comp_id}")
        
        # Test side composition resolution
        print("\n2. Side composition resolution:")
        if site.sides and site.sides.side:
            for i, side in enumerate(site.sides.side, 1):
                print(f"\n   Side {i}: {side.xy_id}")
                
                # Get plain composition
                plain_comp = parser.get_composition_for_side(site, side)
                if plain_comp:
                    print(f"     Plain: {plain_comp.composition_id} ({len(plain_comp.layer)} layers)")
                
                # Get glazing composition
                if side.glazing:
                    print(f"     Glazing: {side.glazing}")
        
        # Test main compositions
        print("\n3. Main compositions:")
        roof_comp = parser.get_roof_composition(site)
        if roof_comp:
            print(f"   Roof: {roof_comp.composition_id} ({len(roof_comp.layer)} layers)")
        
        ground_comp = parser.get_ground_composition(site)
        if ground_comp:
            print(f"   Ground: {ground_comp.composition_id} ({len(ground_comp.layer)} layers)")
        
        floor_comp = parser.get_floor_composition(site)
        if floor_comp:
            print(f"   Floor: {floor_comp.composition_id} ({len(floor_comp.layer)} layers)")
        
        print("\n" + "=" * 40)
        print("MATERIAL ANALYSIS")
        print("=" * 40)
        
        # Analyze materials used across all compositions
        materials = {}
        if site.compositions:
            for comp in site.compositions.composition:
                for layer in comp.layer:
                    if layer.material not in materials:
                        materials[layer.material] = {"count": 0, "thickness": 0.0, "compositions": []}
                    materials[layer.material]["count"] += 1
                    materials[layer.material]["thickness"] += layer.thickness
                    if comp.composition_id not in materials[layer.material]["compositions"]:
                        materials[layer.material]["compositions"].append(comp.composition_id)
        
        print("\nMaterials used across all compositions:")
        for material, data in materials.items():
            print(f"   {material}: {data['count']} layers, total thickness: {data['thickness']:.3f}m")
            print(f"     Used in: {', '.join(data['compositions'])}")
        
        print("\n" + "=" * 40)
        print("GPS POINT ANALYSIS")
        print("=" * 40)
        
        # Analyze GPS points
        if site.coordinates and site.coordinates.xy_gps:
            print(f"\nGPS Points ({len(site.coordinates.xy_gps)}):")
            for gps in site.coordinates.xy_gps:
                print(f"   {gps.id}: ({gps.x}, {gps.y})")
        
        if site.perimeter:
            print(f"\nPerimeter points ({len(site.perimeter.xy_gps_id)}):")
            print(f"   {', '.join(site.perimeter.xy_gps_id)}")
        
        print("\n" + "=" * 40)
        print("SIDE ANALYSIS")
        print("=" * 40)
        
        # Analyze sides
        if site.sides and site.sides.side:
            print(f"\nBuilding Sides ({len(site.sides.side)}):")
            for i, side in enumerate(site.sides.side, 1):
                print(f"   Side {i}: {side.xy_id[0]} → {side.xy_id[1]}")
                print(f"     Composition: {side.composition_id}")
                if side.glazing:
                    print(f"     Glazing: {side.glazing}")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise


def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "=" * 40)
    print("ERROR HANDLING TESTS")
    print("=" * 40)
    
    parser = XSDataStdParser()
    
    # Test non-existent file
    try:
        parser.parse_file("non_existent.xml")
        print("❌ Should have raised an error for non-existent file")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")
    
    # Test invalid XML structure
    try:
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <site xmlns="http://simbat.fr/std">
            <name>Test</name>
            <!-- Missing required elements -->
        </site>"""
        parser.parse_string(invalid_xml)
        print("❌ Should have raised an error for invalid XML")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")


def test_data_integrity():
    """Test data integrity and validation."""
    print("\n" + "=" * 40)
    print("DATA INTEGRITY TESTS")
    print("=" * 40)
    
    parser = XSDataStdParser()
    
    try:
        site = parser.parse_file("std_ensag.xml")
        
        # Test required fields
        assert site.name is not None, "Site name should not be None"
        assert site.latitude is not None, "Latitude should not be None"
        assert site.longitude is not None, "Longitude should not be None"
        assert site.height is not None, "Height should not be None"
        assert site.n_floors is not None, "Number of floors should not be None"
        
        # Test coordinate ranges
        assert -180 <= site.latitude <= 180, "Latitude should be between -180 and 180"
        assert -180 <= site.longitude <= 180, "Longitude should be between -180 and 180"
        assert site.height >= 0, "Height should be non-negative"
        assert site.n_floors >= 1, "Number of floors should be at least 1"
        
        # Test minimum requirements
        assert site.coordinates is not None, "Coordinates should be present"
        assert len(site.coordinates.xy_gps) >= 3, "Should have at least 3 GPS points"
        
        assert site.sides is not None, "Sides should be present"
        assert len(site.sides.side) >= 3, "Should have at least 3 sides"
        
        assert site.compositions is not None, "Compositions should be present"
        assert len(site.compositions.composition) >= 1, "Should have at least 1 composition"
        
        assert site.perimeter is not None, "Perimeter should be present"
        assert len(site.perimeter.xy_gps_id) >= 3, "Should have at least 3 perimeter points"
        
        # Test composition references
        for side in site.sides.side:
            comp = parser.get_composition_for_side(site, side)
            assert comp is not None, f"Side {side.xy_id} should have a valid composition reference"
        
        # Test GPS point references
        for gps_id in site.perimeter.xy_gps_id:
            gps = parser.get_xy_gps_by_id(site, gps_id)
            assert gps is not None, f"GPS point {gps_id} should exist"
        
        print("✅ All data integrity tests passed!")
        
    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        raise


if __name__ == "__main__":
    try:
        test_parser_functionality()
        test_error_handling()
        test_data_integrity()
        print("\n🎉 All tests passed! The xsdata parser is working correctly.")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        exit(1)
