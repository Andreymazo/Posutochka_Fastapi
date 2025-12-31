from app.models.user import User
from app.schemas import UserCreate, ClientCreate, LandlordCreate
from app.models.client import Client
from app.models.landlord import Landlord
from app.database import SessionLocal

def create_initial_data():
    db = SessionLocal()

    # Создаем пользователя1
    user1_data = {
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "password_hash": "hashed_password_user",
     
    }
    user_create = UserCreate(**user1_data)
    db_user = User(**user1_data)
    db.add(db_user)
    db.commit()

    # Создаем клиента на пользователя1
    print('db_user.id==============1===================' , db_user.id)
    client_data = {
     
        "first_name": "Jane",
        "last_name": "Smith"
    }
    client_create = ClientCreate(**client_data, user_id=db_user.id)
    db_client = Client(**client_data, user_id=db_user.id)
    db.add(db_client)
    db.commit()

    # Создаем пользователя2
    user2_data = {
        "email": "user2@existing.pay",
        "phone_number": "+1230987563",
        "password_hash": "hashed_password_user2",
     
    }
    user_create = UserCreate(**user2_data)
    db_user = User(**user2_data)
    db.add(db_user)
    db.commit()
    # Создаем арендодателя на пользователя2
    print('db_user.id==============2===================' , db_user.id)
    landlord_data = {
        
        "first_name": "John2",
        "last_name": "Doe2"
    }
    landlord_create = LandlordCreate(**landlord_data, user_id=db_user.id)
    db_landlord = Landlord(**landlord_data, user_id=db_user.id)
    db.add(db_landlord)
    db.commit()

   
 

# Вызов функции для создания начальных данных
create_initial_data()
