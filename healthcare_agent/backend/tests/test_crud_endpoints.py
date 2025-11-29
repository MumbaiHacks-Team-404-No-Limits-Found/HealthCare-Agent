"""Tests for REST CRUD endpoints."""
import pytest
from httpx import AsyncClient


class TestCampsCRUD:
    """Test cases for Camps CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_camp(self, client: AsyncClient, admin_token: str):
        """Test creating a new camp."""
        camp_data = {
            "name": "New Medical Camp",
            "location": "City Hospital",
            "start": "2025-12-15T09:00:00Z",
            "end": "2025-12-15T17:00:00Z",
            "requirements": [
                {"role": "doctor", "count": 2, "slot": "morning"}
            ]
        }
        
        response = await client.post(
            "/api/camps/",
            json=camp_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == camp_data["name"]
        assert data["location"] == camp_data["location"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_camps(self, client: AsyncClient, sample_camp):
        """Test listing all camps."""
        response = await client.get("/api/camps/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == sample_camp["name"]
    
    @pytest.mark.asyncio
    async def test_get_camp(self, client: AsyncClient, sample_camp):
        """Test getting a specific camp by ID."""
        camp_id = str(sample_camp["_id"])
        
        response = await client.get(f"/api/camps/{camp_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == camp_id
        assert data["name"] == sample_camp["name"]
    
    @pytest.mark.asyncio
    async def test_get_camp_not_found(self, client: AsyncClient):
        """Test getting a non-existent camp."""
        fake_id = "507f1f77bcf86cd799439011"
        
        response = await client.get(f"/api/camps/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_camp(self, client: AsyncClient, admin_token: str, sample_camp):
        """Test updating a camp."""
        camp_id = str(sample_camp["_id"])
        
        update_data = {
            "name": "Updated Camp Name",
            "location": sample_camp["location"],
            "start": sample_camp["start"],
            "end": sample_camp["end"],
            "requirements": sample_camp["requirements"]
        }
        
        response = await client.put(
            f"/api/camps/{camp_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Camp Name"
    
    @pytest.mark.asyncio
    async def test_delete_camp(self, client: AsyncClient, admin_token: str, sample_camp):
        """Test deleting a camp."""
        camp_id = str(sample_camp["_id"])
        
        response = await client.delete(
            f"/api/camps/{camp_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify camp is deleted
        get_response = await client.get(f"/api/camps/{camp_id}")
        assert get_response.status_code == 404


class TestVolunteersCRUD:
    """Test cases for Volunteers CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_volunteer(self, client: AsyncClient):
        """Test creating a new volunteer."""
        volunteer_data = {
            "name": "John Doe",
            "phone": "+919800000002",
            "skills": ["doctor"],
            "availability": [
                {"date": "2025-12-01", "slots": ["morning"]}
            ],
            "no_show_rate": 0.1
        }
        
        response = await client.post("/api/volunteers/", json=volunteer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == volunteer_data["name"]
        assert data["phone"] == volunteer_data["phone"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_volunteers(self, client: AsyncClient, sample_volunteer):
        """Test listing all volunteers."""
        response = await client.get("/api/volunteers/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == sample_volunteer["name"]
    
    @pytest.mark.asyncio
    async def test_get_volunteer(self, client: AsyncClient, sample_volunteer):
        """Test getting a specific volunteer by ID."""
        volunteer_id = str(sample_volunteer["_id"])
        
        response = await client.get(f"/api/volunteers/{volunteer_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == volunteer_id
        assert data["name"] == sample_volunteer["name"]
    
    @pytest.mark.asyncio
    async def test_update_volunteer(self, client: AsyncClient, sample_volunteer):
        """Test updating a volunteer."""
        volunteer_id = str(sample_volunteer["_id"])
        
        update_data = {
            "name": "Updated Name",
            "phone": sample_volunteer["phone"],
            "skills": ["doctor", "surgeon"],
            "availability": sample_volunteer["availability"],
            "no_show_rate": 0.15
        }
        
        response = await client.put(
            f"/api/volunteers/{volunteer_id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert "surgeon" in data["skills"]
    
    @pytest.mark.asyncio
    async def test_delete_volunteer(self, client: AsyncClient, admin_token: str, sample_volunteer):
        """Test deleting a volunteer."""
        volunteer_id = str(sample_volunteer["_id"])
        
        response = await client.delete(
            f"/api/volunteers/{volunteer_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify volunteer is deleted
        get_response = await client.get(f"/api/volunteers/{volunteer_id}")
        assert get_response.status_code == 404


class TestAssignmentsCRUD:
    """Test cases for Assignments CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_assignment(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_camp,
        sample_volunteer
    ):
        """Test creating a new assignment."""
        assignment_data = {
            "camp_id": str(sample_camp["_id"]),
            "volunteer_id": str(sample_volunteer["_id"]),
            "role": "doctor",
            "slot": "morning",
            "status": "assigned",
            "is_backup": False
        }
        
        response = await client.post(
            "/api/assignments/",
            json=assignment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["camp_id"] == assignment_data["camp_id"]
        assert data["volunteer_id"] == assignment_data["volunteer_id"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_list_assignments(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_camp,
        sample_volunteer
    ):
        """Test listing assignments with filters."""
        # Create an assignment first
        assignment_data = {
            "camp_id": str(sample_camp["_id"]),
            "volunteer_id": str(sample_volunteer["_id"]),
            "role": "doctor",
            "slot": "morning",
            "status": "assigned",
            "is_backup": False
        }
        
        await client.post(
            "/api/assignments/",
            json=assignment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Test listing by camp_id
        response = await client.get(
            f"/api/assignments/?camp_id={sample_camp['_id']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_update_assignment_status(
        self,
        client: AsyncClient,
        admin_token: str,
        sample_camp,
        sample_volunteer
    ):
        """Test updating assignment status."""
        # Create an assignment
        assignment_data = {
            "camp_id": str(sample_camp["_id"]),
            "volunteer_id": str(sample_volunteer["_id"]),
            "role": "doctor",
            "slot": "morning",
            "status": "assigned",
            "is_backup": False
        }
        
        create_response = await client.post(
            "/api/assignments/",
            json=assignment_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assignment_id = create_response.json()["id"]
        
        # Update status
        response = await client.patch(
            f"/api/assignments/{assignment_id}?status=confirmed",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"

