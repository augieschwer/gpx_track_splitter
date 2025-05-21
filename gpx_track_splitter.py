#!/usr/bin/env python3
"""
GPX Track Splitter

This script takes a GPX file with multiple tracks and splits it into separate
GPX files, one per track, while preserving all metadata and structure.
"""

import sys
import os
import argparse
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from pathlib import Path

def clean_filename(name):
    """Convert a string to a valid filename by removing invalid characters."""
    if not name:
        return "unnamed_track"
    # Replace invalid filename characters with underscores
    cleaned = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Replace spaces with underscores and remove any multiple underscores
    cleaned = re.sub(r'\s+', "_", cleaned)
    cleaned = re.sub(r'_+', "_", cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip("_")
    
    return cleaned or "unnamed_track"

def extract_namespaces(root):
    """Extract namespace information from the root element."""
    namespaces = {}
    for key, value in root.attrib.items():
        if key.startswith("xmlns:"):
            prefix = key.split(":")[1]
            namespaces[prefix] = value
        elif key == "xmlns":
            namespaces[""] = value
    return namespaces

def register_namespaces(namespaces):
    """Register all namespaces with ElementTree for proper XML output."""
    for prefix, uri in namespaces.items():
        if prefix:
            ET.register_namespace(prefix, uri)
        else:
            ET.register_namespace("", uri)

def get_track_name(track, index):
    """Extract track name or generate a default one based on index."""
    name_elem = track.find(".//name")
    if name_elem is not None and name_elem.text:
        return name_elem.text
    
    # Look for a time element to use in the name
    time_elem = track.find(".//time")
    if time_elem is not None and time_elem.text:
        try:
            time_str = time_elem.text
            # Parse ISO format and convert to simple format
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return f"Track_{dt.strftime('%Y%m%d_%H%M%S')}"
        except (ValueError, TypeError):
            pass
    
    # Default name with index
    return f"Track_{index + 1}"

def split_gpx_file(input_file):
    """
    Split a GPX file with multiple tracks into separate files, one per track.
    
    Args:
        input_file: Path to the input GPX file.
    
    Returns:
        List of paths to the created output files.
    """
    try:
        # Parse the GPX file
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # Extract and register namespaces
        namespaces = extract_namespaces(root)
        register_namespaces(namespaces)
        
        # Default namespace for GPX
        ns = {'gpx': namespaces.get('', 'http://www.topografix.com/GPX/1/1')}
        
        # Find all tracks in the GPX file
        tracks = root.findall('.//gpx:trk', ns)
        
        if not tracks:
            print(f"No tracks found in {input_file}")
            return []
        
        print(f"Found {len(tracks)} tracks in {input_file}")
        
        # Create output directory if needed
        output_files = []
        input_path = Path(input_file)
        
        # Extract global metadata and waypoints to include in each output file
        metadata = root.find('./gpx:metadata', ns)
        waypoints = root.findall('./gpx:wpt', ns)
        
        # Create the base output element structure (without tracks)
        for i, track in enumerate(tracks):
            # Create a new root element with the same attributes as the original
            new_root = ET.Element(root.tag, root.attrib)
            
            # Add metadata if present
            if metadata is not None:
                new_root.append(metadata)
            
            # Add waypoints if present
            for wpt in waypoints:
                new_root.append(wpt)
            
            # Add the current track
            new_root.append(track)
            
            # Get track name for the output file
            track_name = get_track_name(track, i)
            clean_name = clean_filename(track_name)
            
            # Create the output file path
            output_file = input_path.with_name(f"{input_path.stem}_{clean_name}.gpx")
            
            # Create a new ElementTree and write it to the output file
            new_tree = ET.ElementTree(new_root)
            new_tree.write(output_file, encoding='UTF-8', xml_declaration=True)
            
            output_files.append(output_file)
            print(f"Created: {output_file}")
        
        return output_files
    
    except ET.ParseError as e:
        print(f"Error parsing GPX file: {e}")
        return []
    except Exception as e:
        print(f"Error splitting GPX file: {e}")
        return []

def main():
    """Main function to parse arguments and run the GPX splitter."""
    parser = argparse.ArgumentParser(description="Split a GPX file with multiple tracks into separate GPX files")
    parser.add_argument("input_file", help="Path to the input GPX file")
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Check if input file has .gpx extension
    if not args.input_file.lower().endswith('.gpx'):
        print(f"Warning: Input file '{args.input_file}' does not have .gpx extension. Proceeding anyway.")
    
    # Split the GPX file
    output_files = split_gpx_file(args.input_file)
    
    if output_files:
        print(f"\nSuccessfully split {args.input_file} into {len(output_files)} separate GPX files.")
    else:
        print(f"\nFailed to split {args.input_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()

