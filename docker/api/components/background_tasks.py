# Background Tasks Component - For S3 event processing
import asyncio
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from shared.aws_clients import AWSClientManager
from components.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class BackgroundTaskProcessor:
    """Background task processor for S3 events and other async operations"""
    
    def __init__(self, aws_clients: AWSClientManager, document_processor: DocumentProcessor):
        self.aws_clients = aws_clients
        self.document_processor = document_processor
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start background task processor"""
        if self.running:
            logger.warning("Background processor already running")
            return
        
        self.running = True
        logger.info("Starting background task processor...")
        
        # Start S3 event processor
        s3_task = asyncio.create_task(self._process_s3_events())
        self.tasks.append(s3_task)
        
        # Start other background tasks as needed
        # cleanup_task = asyncio.create_task(self._cleanup_old_files())
        # self.tasks.append(cleanup_task)
        
        logger.info("Background task processor started")
    
    async def stop(self):
        """Stop background task processor"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping background task processor...")
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("Background task processor stopped")
    
    async def _process_s3_events(self):
        """Process S3 events in background (simulating Lambda functionality)"""
        logger.info("Starting S3 event processor...")
        
        while self.running:
            try:
                # In a real implementation, this would:
                # 1. Poll SQS for S3 events
                # 2. Process each event
                # 3. Handle errors and retries
                
                # For now, we'll simulate by checking for new S3 objects
                await self._check_for_new_s3_objects()
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("S3 event processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in S3 event processor: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_for_new_s3_objects(self):
        """Check for new S3 objects to process"""
        try:
            # This is a simplified version - in production you'd use SQS
            s3_bucket = os.environ.get('S3_DATA_BUCKET', 'realistic-demo-pretamane-data')
            
            # List objects in the documents/ prefix
            response = self.aws_clients.s3_client.list_objects_v2(
                Bucket=s3_bucket,
                Prefix='documents/',
                MaxKeys=10
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Check if object was created recently (last 5 minutes)
                    if self._is_recent_object(obj['LastModified']):
                        await self._process_s3_object(s3_bucket, obj['Key'])
                        
        except Exception as e:
            logger.error(f"Error checking for new S3 objects: {str(e)}")
    
    def _is_recent_object(self, last_modified) -> bool:
        """Check if object was created recently"""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        return (now - last_modified).total_seconds() < 300  # 5 minutes
    
    async def _process_s3_object(self, bucket: str, key: str):
        """Process a single S3 object"""
        try:
            logger.info(f"Processing S3 object: s3://{bucket}/{key}")
            
            # Process the document
            result = await self.document_processor.process_s3_document(bucket, key)
            
            if 'error' in result:
                logger.error(f"Error processing S3 object {key}: {result['error']}")
            else:
                logger.info(f"Successfully processed S3 object {key}")
                
        except Exception as e:
            logger.error(f"Error processing S3 object {key}: {str(e)}")
    
    async def _cleanup_old_files(self):
        """Cleanup old temporary files"""
        while self.running:
            try:
                # Implement cleanup logic here
                # For example, remove files older than 24 hours from /tmp
                logger.debug("Running cleanup task...")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(3600)
    
    async def add_task(self, task_func, *args, **kwargs):
        """Add a new background task"""
        task = asyncio.create_task(task_func(*args, **kwargs))
        self.tasks.append(task)
        return task
    
    def get_status(self) -> Dict[str, Any]:
        """Get background processor status"""
        return {
            'running': self.running,
            'active_tasks': len(self.tasks),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
