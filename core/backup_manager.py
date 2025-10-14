"""
Backup Manager
Saves emails to JSON files before deletion for safety and undo functionality
"""

import json
import os
from datetime import datetime
from pathlib import Path


class BackupManager:
    """Manages email backups before deletion"""
    
    def __init__(self, backup_dir='email_backups'):
        """Initialize backup manager with backup directory"""
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        print(f"💾 Backup directory: {self.backup_dir.absolute()}")
    
    def create_backup(self, emails, proposal_id=None):
        """
        Create a backup of emails before deletion
        
        Args:
            emails (list): List of email objects to backup
            proposal_id (str): Optional ID for this backup batch
            
        Returns:
            str: Path to backup file
        """
        if not proposal_id:
            proposal_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_file = self.backup_dir / f"backup_{proposal_id}.json"
        
        # Prepare backup data
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'proposal_id': proposal_id,
            'email_count': len(emails),
            'emails': []
        }
        
        # Save each email's data
        for email in emails:
            email_backup = {
                'id': email.get('id'),
                'subject': email.get('subject'),
                'from': email.get('from'),
                'receivedDateTime': email.get('receivedDateTime'),
                'bodyPreview': email.get('bodyPreview'),
                'hasAttachments': email.get('hasAttachments'),
                'isRead': email.get('isRead'),
                'inferenceClassification': email.get('inferenceClassification', 'other')
            }
            backup_data['emails'].append(email_backup)
        
        # Write to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Backup created: {backup_file.name}")
        print(f"   Backed up {len(emails)} emails")
        
        return str(backup_file)
    
    def get_backup(self, proposal_id):
        """
        Retrieve a backup by proposal ID
        
        Args:
            proposal_id (str): The proposal ID
            
        Returns:
            dict: Backup data or None if not found
        """
        backup_file = self.backup_dir / f"backup_{proposal_id}.json"
        
        if not backup_file.exists():
            print(f"❌ Backup not found: {backup_file.name}")
            return None
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        print(f"📥 Loaded backup: {backup_file.name}")
        return backup_data
    
    def list_backups(self):
        """List all available backups"""
        backups = sorted(self.backup_dir.glob('backup_*.json'))
        
        if not backups:
            print("📦 No backups found")
            return []
        
        print(f"📦 Found {len(backups)} backup(s):")
        backup_list = []
        
        for backup_file in backups:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            backup_info = {
                'file': backup_file.name,
                'proposal_id': data['proposal_id'],
                'timestamp': data['timestamp'],
                'email_count': data['email_count']
            }
            backup_list.append(backup_info)
            
            print(f"   • {backup_file.name}: {data['email_count']} emails at {data['timestamp']}")
        
        return backup_list
    
    def get_backup_summary(self, proposal_id):
        """Get a summary of what's in a backup"""
        backup_data = self.get_backup(proposal_id)
        
        if not backup_data:
            return None
        
        subjects = [email['subject'][:50] for email in backup_data['emails'][:5]]
        
        summary = {
            'timestamp': backup_data['timestamp'],
            'email_count': backup_data['email_count'],
            'sample_subjects': subjects,
            'has_more': backup_data['email_count'] > 5
        }
        
        return summary


# Test the backup manager
if __name__ == "__main__":
    print("="*100)
    print("💾 BACKUP MANAGER TEST")
    print("="*100 + "\n")
    
    # Create test emails
    test_emails = [
        {
            'id': 'test123',
            'subject': 'Test Email 1',
            'from': {'emailAddress': {'address': 'test@example.com', 'name': 'Tester'}},
            'receivedDateTime': '2024-10-14T10:00:00Z',
            'bodyPreview': 'This is a test email',
            'hasAttachments': False,
            'isRead': True
        },
        {
            'id': 'test456',
            'subject': 'Test Email 2',
            'from': {'emailAddress': {'address': 'test2@example.com', 'name': 'Tester 2'}},
            'receivedDateTime': '2024-10-14T11:00:00Z',
            'bodyPreview': 'Another test email',
            'hasAttachments': True,
            'isRead': False
        }
    ]
    
    # Create backup manager
    manager = BackupManager()
    
    # Create a backup
    backup_file = manager.create_backup(test_emails, proposal_id='test_20241014')
    
    # List backups
    print()
    manager.list_backups()
    
    # Retrieve backup
    print()
    backup_data = manager.get_backup('test_20241014')
    print(f"\n✅ Retrieved backup with {backup_data['email_count']} emails")
    
    # Get summary
    print()
    summary = manager.get_backup_summary('test_20241014')
    print(f"📊 Backup Summary:")
    print(f"   Timestamp: {summary['timestamp']}")
    print(f"   Emails: {summary['email_count']}")
    print(f"   Sample subjects: {summary['sample_subjects']}")
    
    print("\n" + "="*100)
    print("✅ Backup Manager Test Complete!")
    print("="*100)