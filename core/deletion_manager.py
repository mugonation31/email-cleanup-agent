"""
Deletion Manager
Safely deletes emails with backup and undo functionality
"""

import requests
from core.backup_manager import BackupManager
from datetime import datetime


class DeletionManager:
    """Manages email deletion with safety features"""
    
    def __init__(self, outlook_connector):
        """
        Initialize deletion manager
        
        Args:
            outlook_connector: OutlookConnector instance with valid token
        """
        self.outlook = outlook_connector
        self.backup_manager = BackupManager()
        self.last_deletion = None
        
        print("🗑️ Deletion Manager initialized")
    
    def delete_emails(self, emails, proposal_id=None, create_backup=True):
        """
        Delete emails with backup and inbox tracking
        
        Args:
            emails (list): List of email objects to delete
            proposal_id (str): Optional ID for this deletion batch
            create_backup (bool): Whether to create backup before deletion
            
        Returns:
            dict: Deletion results with success/failure counts and inbox stats
        """
        if not emails:
            print("⚠️ No emails to delete")
            return {'success': 0, 'failed': 0, 'errors': []}
        
        if not proposal_id:
            proposal_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n🗑️ Starting deletion process for {len(emails)} emails...")
        
        # Step 0: Get inbox count BEFORE deletion
        count_before = self.get_inbox_count()
        if count_before:
            print(f"📊 Current inbox: {count_before:,} emails")
        
        # Step 1: Create backup
        backup_file = None
        if create_backup:
            print(f"💾 Creating backup first...")
            backup_file = self.backup_manager.create_backup(emails, proposal_id)
            print(f"✅ Backup saved: {backup_file}")
        
        # Step 2: Delete emails one by one
        results = {
            'proposal_id': proposal_id,
            'backup_file': backup_file if create_backup else None,
            'total': len(emails),
            'success': 0,
            'failed': 0,
            'errors': [],
            'deleted_ids': []
        }
        
        print(f"\n🗑️ Deleting emails...")
        
        for i, email in enumerate(emails, 1):
            email_id = email.get('id')
            subject = email.get('subject', 'No Subject')[:50]
            
            try:
                # Call Microsoft Graph API to delete
                success = self._delete_single_email(email_id)
                
                if success:
                    results['success'] += 1
                    results['deleted_ids'].append(email_id)
                    print(f"   ✅ {i}/{len(emails)}: Deleted - {subject}")
                else:
                    results['failed'] += 1
                    results['errors'].append({'email_id': email_id, 'subject': subject, 'error': 'Delete failed'})
                    print(f"   ❌ {i}/{len(emails)}: Failed - {subject}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'email_id': email_id, 'subject': subject, 'error': str(e)})
                print(f"   ❌ {i}/{len(emails)}: Error - {subject} ({e})")
        
        # Step 3: Get inbox count AFTER deletion
        count_after = self.get_inbox_count()
        
        # Calculate stats
        if count_before and count_after:
            actually_deleted = count_before - count_after
            progress = (actually_deleted / count_before) * 100 if count_before > 0 else 0
            
            results['count_before'] = count_before
            results['count_after'] = count_after
            results['progress'] = round(progress, 2)
        
        # Store for potential undo
        self.last_deletion = results
        
        print(f"\n✅ Deletion complete!")
        print(f"   Succeeded: {results['success']}")
        print(f"   Failed: {results['failed']}")
        
        if count_before and count_after:
            print(f"\n📊 Inbox Status:")
            print(f"   Before: {count_before:,} emails")
            print(f"   After: {count_after:,} emails")
            print(f"   Progress: {progress:.2f}% of inbox cleaned")
        
        return results
        
    def _delete_single_email(self, email_id):
        """
        Delete a single email via Microsoft Graph API
        
        Args:
            email_id (str): The email ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.outlook.token:
            print("❌ No authentication token!")
            return False
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
        headers = {
            'Authorization': f'Bearer {self.outlook.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.delete(endpoint, headers=headers, timeout=10)
            
            # 204 No Content = success
            if response.status_code == 204:
                return True
            else:
                print(f"⚠️ Delete returned status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Delete request failed: {e}")
            return False
    
    def get_deletion_summary(self):
        """Get summary of last deletion"""
        if not self.last_deletion:
            return None
        
        return {
            'proposal_id': self.last_deletion['proposal_id'],
            'total': self.last_deletion['total'],
            'success': self.last_deletion['success'],
            'failed': self.last_deletion['failed'],
            'backup_file': self.last_deletion['backup_file']
        }

    def get_inbox_count(self, folder='OTHER'):
        """Get current email count in folder"""
        try:
            response = self.graph_client.get(
                f'/me/mailFolders/{folder}/messages/$count'
            )
            return response.json() if isinstance(response.json(), int) else 0
        except Exception as e:
            print(f"⚠️ Could not fetch inbox count: {e}")
            return None

# Test the deletion manager (DRY RUN - no actual deletion)
if __name__ == "__main__":
    print("="*100)
    print("🗑️ DELETION MANAGER TEST (DRY RUN)")
    print("="*100 + "\n")
    
    print("ℹ️ This is a dry run test - no actual emails will be deleted")
    print("ℹ️ In real usage, this would connect to Outlook and delete emails")
    
    # Test data
    test_emails = [
        {
            'id': 'test_id_1',
            'subject': 'Test Email 1 - Safe to delete',
            'from': {'emailAddress': {'address': 'test@example.com', 'name': 'Test'}},
            'receivedDateTime': '2024-10-14T10:00:00Z',
            'bodyPreview': 'Test',
            'hasAttachments': False,
            'isRead': True
        }
    ]
    
    print("\n📋 Would delete 1 test email")
    print("   Subject: Test Email 1 - Safe to delete")
    
    # Create backup manager to show backup works
    backup_mgr = BackupManager()
    backup_file = backup_mgr.create_backup(test_emails, proposal_id='dryrun_test')
    
    print(f"\n✅ Backup system working")
    print(f"💾 In real deletion, emails would be backed up to: {backup_file}")
    print(f"🗑️ Then deletion would proceed via Microsoft Graph API")
    
    print("\n" + "="*100)
    print("✅ Deletion Manager Test Complete (Dry Run)")
    print("="*100)
    print("\nℹ️ To enable real deletion, integrate with OutlookConnector")