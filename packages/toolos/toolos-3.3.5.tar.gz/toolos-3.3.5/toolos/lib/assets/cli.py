#!/usr/bin/env python3
"""
BuildTools CLI - Command Line Interface
© 2025 ClayTech
"""

import sys
import os
import argparse
from . import __version__
from sqlsave import SqlSave
from statemachine import StateMachine
from cons import ConsoleEditor
from filewriter import FileWriter, Json

def main():
    parser = argparse.ArgumentParser(
        description='BuildTools CLI - Professional Development Utilities',
        prog='buildtools'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'BuildTools v{__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show BuildTools information')
    
    # File operations
    file_parser = subparsers.add_parser('file', help='File operations')
    file_parser.add_argument('action', choices=['create', 'read', 'write', 'delete'])
    file_parser.add_argument('path', help='File path')
    file_parser.add_argument('--content', help='Content for write operation')
    
    # JSON operations  
    json_parser = subparsers.add_parser('json', help='JSON operations')
    json_parser.add_argument('action', choices=['create', 'read', 'add', 'update', 'delete'])
    json_parser.add_argument('file', help='JSON file path')
    json_parser.add_argument('--key', help='JSON key')
    json_parser.add_argument('--value', help='JSON value')
    
    # Database operations
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_parser.add_argument('action', choices=['save', 'load', 'list', 'delete'])
    db_parser.add_argument('--id', help='Data ID')
    db_parser.add_argument('--data', help='Data to save')
    db_parser.add_argument('--file', help='Database file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    console = ConsoleEditor()
    
    try:
        if args.command == 'info':
            show_info()
            
        elif args.command == 'file':
            handle_file_operations(args, console)
            
        elif args.command == 'json':
            handle_json_operations(args, console)
            
        elif args.command == 'db':
            handle_db_operations(args, console)
            
    except Exception as e:
        console.error(f"Error: {e}")
        sys.exit(1)

def show_info():
    console = ConsoleEditor()
    console.info(f"BuildTools v{__version__}")
    console.success("Professional Python Development Utilities")
    console.warning("\nAvailable Modules:")
    console.success("• SqlSave - Local data persistence")
    console.success("• StateMachine - State management") 
    console.success("• ConsoleEditor - Rich console output")
    console.success("• FileWriter - File operations")
    console.success("• Json - JSON handling")
    console.success("• Gipeo - Hardware integration")
    console.success("• AILogic - AI integration")
    console.info(f"\nDocumentation: https://github.com/claytechnologie/BuildTools")

def handle_file_operations(args, console):
    fw = FileWriter()
    
    if args.action == 'create':
        fw.create_file(args.path)
        console.success(f"Created file: {args.path}")
        
    elif args.action == 'read':
        content = fw.read_file(args.path)
        console.print(f"[bold]Content of {args.path}:[/bold]")
        console.print(content)
        
    elif args.action == 'write':
        if not args.content:
            console.error("--content required for write operation")
            return
        fw.write_file(args.path, args.content)
        console.success(f"Written to: {args.path}")
        
    elif args.action == 'delete':
        fw.delete_file(args.path)
        console.success(f"Deleted: {args.path}")

def handle_json_operations(args, console):
    json_handler = Json()
    
    if args.action == 'create':
        json_handler.create_json_file(args.file)
        console.success(f"Created JSON file: {args.file}")
        
    elif args.action == 'read':
        data = json_handler.read_json_file(args.file)
        console.print(f"[bold]Content of {args.file}:[/bold]")
        console.print(data)
        
    elif args.action == 'add':
        if not args.key or not args.value:
            console.error("--key and --value required for add operation")
            return
        json_handler.add_to_json(args.file, args.key, args.value)
        console.success(f"Added {args.key}: {args.value} to {args.file}")
        
    elif args.action == 'update':
        if not args.key or not args.value:
            console.error("--key and --value required for update operation")
            return
        json_handler.update_json_key(args.file, args.key, args.value)
        console.success(f"Updated {args.key} in {args.file}")
        
    elif args.action == 'delete':
        if not args.key:
            console.error("--key required for delete operation")
            return
        json_handler.delete_json_key(args.file, args.key)
        console.success(f"Deleted {args.key} from {args.file}")

def handle_db_operations(args, console):
    db_file = args.file or "buildtools.db"
    db = SqlSave(db_file)
    
    if args.action == 'save':
        if not args.id or not args.data:
            console.error("--id and --data required for save operation")
            return
        db.save(data=args.data, id=args.id)
        console.success(f"Saved data with ID: {args.id}")
        
    elif args.action == 'load':
        if not args.id:
            console.error("--id required for load operation")
            return
        data = db.load(id=args.id)
        console.print(f"[bold]Data for ID '{args.id}':[/bold]")
        console.print(data)
        
    elif args.action == 'list':
        data = db.load_all()
        console.print("[bold]All stored data:[/bold]")
        for item in data:
            console.print(f"ID: {item['id']} | Data: {item['data']}")
            
    elif args.action == 'delete':
        if not args.id:
            console.error("--id required for delete operation")
            return
        db.delete(id=args.id)
        console.success(f"Deleted data with ID: {args.id}")

if __name__ == '__main__':
    main()
