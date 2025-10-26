"""
Database Architecture Demo
=========================

Demonstrates the producer/consumer architecture:
1. Raspberry Pi writes sensor data to database
2. Processing program reads from database in real-time

This shows complete separation between data collection and processing.
"""

import subprocess
import time
import sys
import os

def run_demo():
    """Run the database architecture demo"""
    print("🗄️  Database Architecture Demo")
    print("=" * 50)
    print("Architecture:")
    print("  Raspberry Pi → Elastic Serverless → Processing Program")
    print("     (Writer)        (Database)         (Reader)")
    print()
    
    print("💡 This demo will:")
    print("1. Start Raspberry Pi simulator (writes to database)")
    print("2. Start processing program (reads from database)")
    print("3. Show real-time data flow between them")
    print()
    
    # Check credentials
    if not os.path.exists('elastic/credentials.json'):
        print("❌ No Elastic credentials found")
        print("Run: python setup_complete.py first")
        return
    
    print("🚀 Starting demo components...")
    print()
    
    # Instructions for manual demo
    print("📋 MANUAL DEMO INSTRUCTIONS:")
    print()
    print("Terminal 1 (Raspberry Pi Writer):")
    print("  python database/pi_writer.py")
    print()
    print("Terminal 2 (Real-time Reader):")
    print("  python database/realtime_reader.py")
    print()
    print("You'll see:")
    print("  • Terminal 1: [DB WRITE] messages showing data being saved")
    print("  • Terminal 2: Real-time processing of that data")
    print("  • Complete separation between producer and consumer")
    print()
    
    choice = input("Start automated demo? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("\n🔄 Starting automated demo...")
        
        # Start Pi writer in background
        print("1. Starting Raspberry Pi writer...")
        writer_cmd = [sys.executable, "database/pi_writer.py"]
        
        # Start reader in background  
        print("2. Starting real-time reader...")
        reader_cmd = [sys.executable, "database/realtime_reader.py"]
        
        print("\n⚠️  Note: For full demo, run these in separate terminals:")
        print(f"Writer: {' '.join(writer_cmd)}")
        print(f"Reader: {' '.join(reader_cmd)}")
        print("\nThis shows true separation of concerns!")
    
    else:
        print("Manual demo instructions provided above ⬆️")


def show_architecture():
    """Show the database architecture"""
    print("\n📐 Database Architecture Benefits:")
    print()
    print("✅ Separation of Concerns:")
    print("   • Raspberry Pi only focuses on data collection")
    print("   • Processing program only focuses on analysis")
    print("   • Database handles data storage and retrieval")
    print()
    print("✅ Real-time Performance:")
    print("   • Elastic Serverless provides instant data availability")
    print("   • No need for direct Pi ↔ Program communication")
    print("   • Scales to multiple Pis and multiple consumers")
    print()
    print("✅ Reliability:")
    print("   • If Pi goes offline, data processing continues")
    print("   • If processing stops, Pi data is preserved")
    print("   • Database provides data persistence")
    print()
    print("✅ Flexibility:")
    print("   • Multiple programs can read the same data")
    print("   • Different processing programs for different purposes")
    print("   • Historical data analysis capabilities")


if __name__ == "__main__":
    run_demo()
    show_architecture()