"""
VeriChain CLI - Command-line interface for verification and management.

Usage:
    verichain verify <packet.vchain> [--ca <ca.pem>]
    verichain list-anchors
    verichain stats
    verichain generate-keys --key-id <id> --output <path>
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from .packager import PacketPackager
from .signer import ECDSASigner
from .hasher import sha3_hash


def verify_command(args):
    """Verify a .vchain container."""
    container_path = args.container
    
    if not Path(container_path).exists():
        print(f"❌ Error: Container not found: {container_path}")
        return 1
    
    print(f"🔍 Verifying container: {container_path}")
    print()
    
    packager = PacketPackager()
    report = packager.verify_container(container_path)
    
    if report['valid']:
        print("✅ Container is VALID")
        print()
        print("📋 Details:")
        details = report.get('details', {})
        print(f"  Decision ID: {details.get('decision_id')}")
        print(f"  Timestamp:   {details.get('timestamp')}")
        print(f"  Issuer:      {details.get('issuer', {}).get('entity_id')}")
        print(f"  Node:        {details.get('issuer', {}).get('node_id')}")
        print(f"  Model:       {details.get('model', {}).get('id')} v{details.get('model', {}).get('version')}")
        print(f"  Key ID:      {details.get('key_id')}")
        
        # Check for anchor
        if args.check_anchor:
            print()
            print("🔗 Checking anchor...")
            
            # Import anchor verifier
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'anchor-worker'))
            from worker import AnchorVerifier
            
            verifier = AnchorVerifier()
            packet = packager.extract_packet(container_path)
            packet_hash = sha3_hash(json.dumps(packet, sort_keys=True, separators=(',', ':')))
            
            anchor_report = verifier.verify_receipt(details.get('decision_id'), packet_hash)
            
            if anchor_report['valid']:
                print("✅ Anchor is VALID")
                anchor_details = anchor_report.get('details', {})
                print(f"  Merkle Root: {anchor_details.get('merkle_root')}")
                print(f"  Segment ID:  {anchor_details.get('segment_id')}")
                print(f"  Anchor Time: {anchor_details.get('anchor_time')}")
            else:
                print("⚠️  Anchor not found or invalid")
                for error in anchor_report.get('errors', []):
                    print(f"    - {error}")
        
        return 0
    else:
        print("❌ Container is INVALID")
        print()
        print("🚨 Errors:")
        for error in report.get('errors', []):
            print(f"  - {error}")
        
        if report.get('warnings'):
            print()
            print("⚠️  Warnings:")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        return 1


def list_anchors_command(args):
    """List anchor batches."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'anchor-worker'))
    from worker import AnchorVerifier
    
    verifier = AnchorVerifier()
    anchors = verifier.list_anchors()
    
    if not anchors:
        print("No anchors found.")
        return 0
    
    print(f"📦 Found {len(anchors)} anchor batches:")
    print()
    
    for i, anchor in enumerate(anchors[:args.limit], 1):
        print(f"{i}. {anchor['segment_id']}")
        print(f"   Root:    {anchor['merkle_root'][:16]}...")
        print(f"   Time:    {anchor['anchor_time']}")
        print(f"   Packets: {anchor['packet_count']}")
        print()
    
    return 0


def stats_command(args):
    """Show system statistics."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'anchor-worker'))
    from worker import AnchorVerifier
    
    verifier = AnchorVerifier()
    anchors = verifier.list_anchors()
    
    total_packets = sum(a['packet_count'] for a in anchors)
    
    print("📊 VeriChain Statistics")
    print()
    print(f"Total Anchors:  {len(anchors)}")
    print(f"Total Packets:  {total_packets}")
    
    if anchors:
        latest = anchors[0]
        print()
        print("Latest Anchor:")
        print(f"  Segment ID:   {latest['segment_id']}")
        print(f"  Merkle Root:  {latest['merkle_root'][:32]}...")
        print(f"  Time:         {latest['anchor_time']}")
        print(f"  Packets:      {latest['packet_count']}")
    
    return 0


def generate_keys_command(args):
    """Generate signing keys."""
    key_id = args.key_id
    output_path = Path(args.output)
    
    print(f"🔑 Generating ECDSA key pair...")
    print(f"   Key ID: {key_id}")
    
    # Generate key
    signer = ECDSASigner(key_id)
    
    # Save private key
    private_key_path = output_path / f"{key_id}.pem"
    public_key_path = output_path / f"{key_id}.pub.pem"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    password = None
    if args.password:
        password = args.password.encode('utf-8')
    
    signer.save_private_key(str(private_key_path), password)
    
    # Save public key
    with open(public_key_path, 'w') as f:
        f.write(signer.get_public_key_pem())
    
    print(f"✅ Keys generated:")
    print(f"   Private: {private_key_path}")
    print(f"   Public:  {public_key_path}")
    
    if not password:
        print()
        print("⚠️  Warning: Private key is NOT encrypted!")
        print("   Use --password to encrypt the private key.")
    
    return 0


def extract_command(args):
    """Extract packet from container."""
    container_path = args.container
    
    if not Path(container_path).exists():
        print(f"❌ Error: Container not found: {container_path}")
        return 1
    
    packager = PacketPackager()
    packet = packager.extract_packet(container_path)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(packet, f, indent=2)
        print(f"✅ Packet extracted to: {args.output}")
    else:
        print(json.dumps(packet, indent=2))
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VeriChain CLI - Verifiable Decision Ledger",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a .vchain container')
    verify_parser.add_argument('container', help='Path to .vchain file')
    verify_parser.add_argument('--ca', help='Path to CA certificate')
    verify_parser.add_argument('--check-anchor', action='store_true', help='Check Merkle anchor')
    verify_parser.set_defaults(func=verify_command)
    
    # List anchors command
    list_parser = subparsers.add_parser('list-anchors', help='List anchor batches')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number to show')
    list_parser.set_defaults(func=list_anchors_command)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    stats_parser.set_defaults(func=stats_command)
    
    # Generate keys command
    keys_parser = subparsers.add_parser('generate-keys', help='Generate signing keys')
    keys_parser.add_argument('--key-id', required=True, help='Key identifier')
    keys_parser.add_argument('--output', required=True, help='Output directory')
    keys_parser.add_argument('--password', help='Password to encrypt private key')
    keys_parser.set_defaults(func=generate_keys_command)
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract packet from container')
    extract_parser.add_argument('container', help='Path to .vchain file')
    extract_parser.add_argument('--output', help='Output file (default: stdout)')
    extract_parser.set_defaults(func=extract_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
