import pytest
from app.main import app
from app.services.roles import get_current_landlord

@pytest.mark.asyncio
async def test_update_apartment_ownership(
    client, 
    db_session,              # Добавили сессию для синхронизации
    created_apartment,       
    mock_landlord_profile    
):
    # Теперь и created_apartment, и mock_landlord_profile 
    # гарантированно находятся в db_session

    async def override_get_current_landlord():
        # Важно: объект уже должен быть загружен с .landlord
        return mock_landlord_profile

    app.dependency_overrides[get_current_landlord] = override_get_current_landlord
    
    try:
        update_data = {"name": "Взломанное название"}
        response = await client.patch(
            f"/apartments/{created_apartment.id}", 
            json=update_data
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Вы можете редактировать только свои объекты"
    finally:
        # Убираем только наш специфичный оверрайд роли. 
        # Общий оверрайд сессии почистит сама фикстура db_session.
        del app.dependency_overrides[get_current_landlord]
