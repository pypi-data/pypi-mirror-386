"""Provides Methods for handling attachments."""
from servicepytan.requests import Endpoint

class JobAttachments(Endpoint):
    """Get attachments for a specific job."""
    
    def __init__(self, conn=None):
        """Initialize with job ID and connection."""
        super().__init__(
            folder="forms",
            endpoint="jobs",
            conn=conn
        ),
        self.attachments = []

    def get_attachments_data(self, job_id):
        """Retrieve attachments for the specified job."""
        response = self.get_all(id=job_id, modifier="attachments")
        self.attachments = response.get("data", [])
        return self.attachments
    
    def download_attachments(self):
        """Download all attachments for the specified job."""
        downloaded_files = []
        for attachment in self.attachments:
            response = self.get_all(id=attachment["id"], modifier="download")
            if response and "data" in response:
                downloaded_files.append(response["data"])
        return downloaded_files
