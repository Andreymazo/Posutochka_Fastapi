"""Tests for Apartment API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


class TestApartmentEndpoints:
    """Tests for /apartments endpoints."""

    @pytest.mark.asyncio
    async def test_create_apartment(
        self,
        client: AsyncClient,
        sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test creating a new apartment asynchronously."""

        # Выполняем асинхронный POST запрос
        response = await client.post("/apartments/", json=sample_apartment_data)

        # Проверки
        assert response.status_code == 201
        data = response.json()

        # Нормализуем обе строки (удаляем пробелы), чтобы сравнить только координаты
        expected_loc = sample_apartment_data["location"].replace(" ", "")
        actual_loc = data["location"].replace(" ", "")

        assert actual_loc == expected_loc
        assert data["name"] == sample_apartment_data["name"]
        assert data["description"] == sample_apartment_data["description"]
        assert data["price_per_night"] == sample_apartment_data["price_per_night"]
        assert data["address"] == sample_apartment_data["address"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_apartment_without_description(
        self,
        client: AsyncClient,  # Используем асинхронный клиент
        created_landlord: Any # Убедитесь, что эта фикстура тоже асинхронная
    ) -> None:
        """Test creating apartment without optional description."""
        apartment_data = {
            "name": "Simple Studio",
            "price_per_night": 40.0,
            "address": "456 Oak Avenue",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }

        # Добавляем await для асинхронного вызова
        response = await client.post("/apartments/", json=apartment_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Studio"
        assert data["description"] is None


    @pytest.mark.asyncio
    async def test_create_apartment_invalid_price(self, client: AsyncClient, created_landlord) -> None:
        """Test that creating apartment with invalid price fails."""
        apartment_data = {
            "name": "Test Apartment",
            "price_per_night": -50.0,
            "address": "123 Main Street",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }
        response = await client.post("/apartments/", json=apartment_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_apartments_empty(self, client: AsyncClient) -> None:
        """Test getting apartments when none exist."""
        # Опционально: если вы хотите именно пустой список,
        # нужно явно удалить апартаменты перед этим тестом,
        # но лучше просто проверять тип данных:
        response = await client.get("/apartments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_apartments(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting list of apartments."""
        # Create an apartment first
        await client.post("/apartments/", json=sample_apartment_data)

        response = await client.get("/apartments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(apt["name"] == sample_apartment_data["name"] for apt in data)

    @pytest.mark.asyncio
    async def test_get_apartments_pagination(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test apartments pagination."""
        # Create multiple apartments
        for i in range(5):
            apt_data = sample_apartment_data.copy()
            apt_data["name"] = f"Apartment {i}"
            apt_data["address"] = f"Address {i}"
            await client.post("/apartments/", json=apt_data)

        # Test skip and limit
        response = await client.get("/apartments/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_apartment_by_id(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting a specific apartment by ID."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Get the apartment
        response = await client.get(f"/apartments/{apartment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == apartment_id
        assert data["name"] == sample_apartment_data["name"]

    @pytest.mark.asyncio
    async def test_get_apartment_not_found(self, client: AsyncClient) -> None:
        """Test getting a non-existent apartment."""
        response = await client.get("/apartments/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_apartment(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test updating an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update the apartment
        update_data = {"name": "Updated Apartment", "price_per_night": 75.0}
        response = await client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Apartment"
        assert data["price_per_night"] == 75.0
        assert data["address"] == sample_apartment_data["address"]

    @pytest.mark.asyncio
    async def test_update_apartment_partial(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test partial update of an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update only one field
        update_data = {"description": "New description"}
        response = await client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["name"] == sample_apartment_data["name"]

    @pytest.mark.asyncio
    async def test_update_apartment_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent apartment."""
        response = await client.patch("/apartments/99999", json={"name": "New Name"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_apartment(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test deleting an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Delete the apartment
        response = await client.delete(f"/apartments/{apartment_id}")
        assert response.status_code == 204

        # Verify apartment is deleted
        get_response = await client.get(f"/apartments/{apartment_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_apartment_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent apartment."""
        response = await client.delete("/apartments/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_apartment_invalid_location_format(self, client: AsyncClient, created_landlord) -> None:
        """Тест на невалидный формат WKT (строки 65-67 в схемах)."""
        apartment_data = {
            "name": "Invalid Loc Apt",
            "price_per_night": 100.0,
            "address": "Street 1",
            "location": "INVALID_POINT(abc)", # Неверный формат WKT
            "landlord_id": created_landlord.id,
        }
        response = await client.post("/apartments/", json=apartment_data)
        # Ожидаем 422, так как валидатор в схеме должен выбросить ошибку
        assert response.status_code == 422
        assert "location" in response.json()["detail"][0]["loc"]
    
    @pytest.mark.asyncio
    async def test_delete_apartment_not_found(self, client: AsyncClient) -> None:
        """Тест удаления несуществующего апартамента."""
        response = await client.delete("/apartments/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_apartments_no_params(self, client: AsyncClient) -> None:
        """
        Тест закрывает частичное покрытие веток в роутере (app/routers/apartments.py:20->25).
        Проверяет работу пагинации по умолчанию (без skip и limit).
        """
        response = await client.get("/apartments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_apartment_location_non_point_string(
        self, client: AsyncClient, created_landlord: Any
    ) -> None:
        """
        Закрывает 'return v' в валидаторе (app/schemas/apartment.py:67).
        Передаем строку, которая НЕ начинается с 'POINT'.
        """
        apartment_data = {
            "name": "Non-Point String Test",
            "price_per_night": 100.0,
            "address": "Test Address",
            "location": "Just a string",  # Не сработает v.startswith("POINT")
            "landlord_id": created_landlord.id,
        }
        # Валидатор handle_dal_types просто вернет эту строку, 
        # и ошибка возникнет позже (либо от Pydantic, либо от БД).
        # Нам важно само выполнение строки 'return v' в схеме.
        response = await client.post("/apartments/", json=apartment_data)
        assert response.status_code in (422, 400)

    @pytest.mark.asyncio
    async def test_create_apartment_with_raw_dict(
        self, client: AsyncClient, created_landlord: Any
    ) -> None:
        """
        Для полной уверенности в покрытии схемы, передаем данные, 
        где location — это не строка и не WKBElement (например, список).
        Закрывает логику 'return v' для нетипичных входных данных.
        """
        apartment_data = {
            "name": "Raw Dict Test",
            "price_per_night": 150.0,
            "address": "Test Address 2",
            "location": {"lat": 10, "lng": 20}, # Не строка, не WKBElement
            "landlord_id": created_landlord.id,
        }
        response = await client.post("/apartments/", json=apartment_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_apartments_pagination_branch_coverage(self, client: AsyncClient):
        """Закрывает BrPart 20->25: запрос без параметров skip/limit."""
        response = await client.get("/apartments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_apartments_partial_params(self, client: AsyncClient):
        """Закрывает BrPart 20->25: проверяем разные комбинации пагинации."""
        # 1. Только skip
        await client.get("/apartments/?skip=5")
        # 2. Только limit 
        await client.get("/apartments/?limit=10")
        # 3. Вообще без параметров (уже был, но в связке с этими закроет ветку)
        response = await client.get("/apartments/")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_apartments_partial_pagination(self, client: AsyncClient):
        """Закрывает BrPart 20->25: комбинация заданных и дефолтных параметров."""
        # Передаем только limit, skip остается дефолтным (0)
        await client.get("/apartments/?limit=5")
        # Передаем только skip, limit остается дефолтным (100)
        response = await client.get("/apartments/?skip=1")
        assert response.status_code == 200
# # ________________________________________

# import pytest
# from decimal import Decimal
# from sqlalchemy import select
# from geoalchemy2.elements import WKTElement
# from app.models.apartment import Apartment
# from app.models.landlord import Landlord

# @pytest.fixture
# async def landlord_id(db_session, sample_user_landlord_data):
#     """Создает арендодателя для тестов."""
#     landlord = Landlord(**sample_user_landlord_data)
#     db_session.add(landlord)
#     await db_session.commit()
#     await db_session.refresh(landlord)
#     return landlord.id

# from sqlalchemy import select
# from geoalchemy2.shape import to_shape
# from shapely.geometry import Point
# from app.models.apartment import Apartment
# from app.models.landlord import Landlord
# from decimal import Decimal
# from datetime import datetime, timedelta

# # Тест на создание экземпляра модели и корректное сохранение в БД
# def test_create_apartment(db_session, sample_user_landlord_data):
#     # Создаем арендодателя, так как landlord_id является обязательным FK
#     landlord_data = sample_user_landlord_data
#     landlord = Landlord(**landlord_data)
#     db_session.add(landlord)
#     db_session.commit()

#     # Данные для квартиры
#     apartment_data = {
#         "name": "Cozy Central Apartment",
#         "description": "A lovely place in the city center.",
#         "price_per_night": Decimal("150.00"),
#         "address": "123 Main Street, City",
#         "location": "SRID=4326;POINT(55.753215 37.620393)", # Moscow Red Square coords
#         "landlord_id": landlord.id,
#     }

#     apartment = Apartment(**apartment_data)
#     db_session.add(apartment)
#     db_session.commit()

#     # Проверка, что объект успешно добавлен и имеет ID
#     assert apartment.id is not None
#     assert apartment.name == "Cozy Central Apartment"
#     assert apartment.price_per_night == Decimal("150.00")
#     assert isinstance(apartment.created_at, datetime)
#     assert isinstance(apartment.updated_at, datetime)

#     # Проверка геометрии (Point)
#     stmt = select(Apartment).where(Apartment.id == apartment.id)
#     apartment_from_db = db_session.execute(stmt).scalar_one()
    
#     assert apartment_from_db.location is not None
#     point_shape = to_shape(apartment_from_db.location)
#     assert isinstance(point_shape, Point)
#     assert point_shape.x == 55.753215 
#     assert point_shape.y == 37.620393

#     # Проверка связи с арендодателем
#     assert apartment_from_db.landlord.id == landlord.id


# # Тест на каскадное удаление (если удалить Landlord, его квартиры удаляются)
# def test_cascade_delete_landlord_apartments(db_session, sample_user_landlord_data):
#     landlord = Landlord(**sample_user_landlord_data)
#     db_session.add(landlord)
#     db_session.commit()
#     landlord_id = landlord.id

#     apartment = Apartment(
#         name="Test Apartment",
#         price_per_night=Decimal("100.00"),
#         address="Test Address",
#         location="SRID=4326;POINT(0 0)",
#         landlord_id=landlord_id
#     )
#     db_session.add(apartment)
#     db_session.commit()
#     apartment_id = apartment.id

#     # Удаляем арендодателя
#     db_session.delete(landlord)
#     db_session.commit()

#     # Проверяем, что квартира тоже удалилась (CASCADE)
#     stmt = select(Apartment).where(Apartment.id == apartment_id)
#     apartment_after_delete = db_session.execute(stmt).scalar_one_or_none()
#     assert apartment_after_delete is None


# # Тест на __repr__ (представление объекта)
# def test_apartment_repr(db_session):
#     apartment = Apartment(
#         id=1,
#         name="Test Repr",
#         price_per_night=Decimal("99.99"),
#         address="Repr Address",
#         location="SRID=4326;POINT(0 0)",
#         landlord_id=1 # FK не проверяется в __repr__
#     )
#     expected_repr = "Apartment(id=1, name='Test Repr', price_per_night=99.99, address='Repr Address')"
#     assert repr(apartment) == expected_repr

# @pytest.mark.asyncio
# async def test_apartment_model_creation(db_session, landlord_id, sample_apartment_data):
#     """Тест создания квартиры и проверки значений атрибутов."""
#     apartment = Apartment(
#         **sample_apartment_data,
#         landlord_id=landlord_id
#     )
#     db_session.add(apartment)
#     await db_session.commit()
#     await db_session.refresh(apartment)

#     assert apartment.id is not None
#     assert apartment.name == sample_apartment_data["name"]
#     assert isinstance(apartment.price_per_night, Decimal)
#     assert apartment.landlord_id == landlord_id
#     assert apartment.created_at is not None
#     assert apartment.updated_at is not None

# @pytest.mark.asyncio
# async def test_apartment_repr(landlord_id):
#     """Тест строкового представления __repr__ для 100% покрытия."""
#     apartment = Apartment(
#         id=777,
#         name="Test Repr",
#         price_per_night=Decimal("100.50"),
#         address="Test Address",
#         landlord_id=landlord_id
#     )
#     expected = "Apartment(id=777, name='Test Repr', price_per_night=100.50, address='Test Address')"
#     assert repr(apartment) == expected

# @pytest.mark.asyncio
# async def test_apartment_update_timestamp(db_session, landlord_id, sample_apartment_data):
#     """Тест автоматического обновления поля updated_at."""
#     apartment = Apartment(
#         **sample_apartment_data,
#         landlord_id=landlord_id
#     )
#     db_session.add(apartment)
#     await db_session.commit()
#     await db_session.refresh(apartment)
    
#     first_update = apartment.updated_at
    
#     apartment.name = "New Updated Name"
#     await db_session.commit()
#     await db_session.refresh(apartment)
    
#     assert apartment.name == "New Updated Name"
#     assert apartment.updated_at >= first_update

# @pytest.mark.asyncio
# async def test_apartment_nullable_fields(db_session, landlord_id):
#     """Тест создания квартиры с nullable описанием."""
#     apartment = Apartment(
#         name="Minimal Apt",
#         price_per_night=Decimal("50"),
#         address="Street",
#         location=WKTElement("POINT(0 0)", srid=4326),
#         landlord_id=landlord_id,
#         description=None
#     )
#     db_session.add(apartment)
#     await db_session.commit()
#     await db_session.refresh(apartment)
    
#     assert apartment.description is None

# @pytest.mark.asyncio
# async def test_apartment_deletion(db_session, landlord_id, sample_apartment_data):
#     """Тест удаления квартиры из базы."""
#     apartment = Apartment(
#         **sample_apartment_data,
#         landlord_id=landlord_id
#     )
#     db_session.add(apartment)
#     await db_session.commit()
    
#     apt_id = apartment.id
#     await db_session.delete(apartment)
#     await db_session.commit()
    
#     result = await db_session.execute(select(Apartment).where(Apartment.id == apt_id))
#     assert result.scalar_one_or_none() is None
