import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class ApplicationTracker:
    def __init__(self):
        self.db_file = "data/applications.json"
        self._ensure_data_dir()
        self.applications = self._load_applications()

    def _ensure_data_dir(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)

    def _load_applications(self) -> List[Dict]:
        """Load applications from JSON file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading applications: {str(e)}")
        return []

    def _save_applications(self):
        """Save applications to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.applications, f, indent=2)
        except Exception as e:
            print(f"Error saving applications: {str(e)}")

    def add_application(self, application_data: Dict) -> Dict:
        """
        Add a new job application
        """
        application = {
            "id": len(self.applications) + 1,
            "company": application_data.get("company"),
            "position": application_data.get("position"),
            "status": "applied",
            "applied_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "notes": application_data.get("notes", ""),
            "url": application_data.get("url", ""),
            "salary_range": application_data.get("salary_range", ""),
            "location": application_data.get("location", ""),
            "contact_info": application_data.get("contact_info", ""),
            "follow_up_dates": []
        }
        
        self.applications.append(application)
        self._save_applications()
        return application

    def update_application(self, app_id: int, updates: Dict) -> Optional[Dict]:
        """
        Update an existing application
        """
        for app in self.applications:
            if app["id"] == app_id:
                app.update(updates)
                app["last_updated"] = datetime.now().isoformat()
                self._save_applications()
                return app
        return None

    def get_application(self, app_id: int) -> Optional[Dict]:
        """Get a specific application by ID"""
        for app in self.applications:
            if app["id"] == app_id:
                return app
        return None

    def get_all_applications(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get all applications, optionally filtered
        """
        if not filters:
            return self.applications

        filtered_apps = self.applications
        
        if 'status' in filters:
            filtered_apps = [app for app in filtered_apps 
                           if app['status'] == filters['status']]
            
        if 'company' in filters:
            filtered_apps = [app for app in filtered_apps 
                           if filters['company'].lower() in app['company'].lower()]
            
        if 'date_range' in filters:
            start_date = datetime.fromisoformat(filters['date_range']['start'])
            end_date = datetime.fromisoformat(filters['date_range']['end'])
            filtered_apps = [app for app in filtered_apps 
                           if start_date <= datetime.fromisoformat(app['applied_date']) <= end_date]
            
        return filtered_apps

    def add_follow_up(self, app_id: int, note: str) -> Optional[Dict]:
        """Add a follow-up note to an application"""
        app = self.get_application(app_id)
        if app:
            follow_up = {
                "date": datetime.now().isoformat(),
                "note": note
            }
            app["follow_up_dates"].append(follow_up)
            self._save_applications()
            return app
        return None

    def delete_application(self, app_id: int) -> bool:
        """Delete an application"""
        for i, app in enumerate(self.applications):
            if app["id"] == app_id:
                self.applications.pop(i)
                self._save_applications()
                return True
        return False

    def get_application_statistics(self) -> Dict:
        """Get statistics about applications"""
        total = len(self.applications)
        statuses = {}
        for app in self.applications:
            status = app["status"]
            statuses[status] = statuses.get(status, 0) + 1
            
        return {
            "total_applications": total,
            "status_breakdown": statuses,
            "success_rate": (statuses.get("accepted", 0) / total) if total > 0 else 0
        }

    def display_applications(self):
        """Display all applications in a Streamlit interface"""
        import streamlit as st
        
        applications = self.get_all_applications()
        if not applications:
            st.write("No job applications tracked yet.")
            return
            
        # Display statistics
        stats = self.get_application_statistics()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Applications", stats["total_applications"])
        with col2:
            success_rate = f"{stats['success_rate']*100:.1f}%"
            st.metric("Success Rate", success_rate)
        with col3:
            in_progress = stats["status_breakdown"].get("applied", 0)
            st.metric("In Progress", in_progress)
            
        # Display applications in a table
        applications_data = []
        for app in applications:
            applications_data.append({
                "Company": app["company"],
                "Position": app["position"],
                "Status": app["status"].capitalize(),
                "Applied Date": app["applied_date"].split("T")[0],
                "Last Updated": app["last_updated"].split("T")[0]
            })
            
        if applications_data:
            st.dataframe(applications_data, use_container_width=True)