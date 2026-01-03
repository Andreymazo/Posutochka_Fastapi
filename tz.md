### 1. Общие требования

- **Цель проекта**: Создание платформы для бронирования апартаментов, где пользователи смогут находить и арендовать жилье на короткий срок.
- **Платформа**: Telegram bot для взаимодействия с пользователями.
- **Масштабируемость**: Проект рассчитан на более миллиона пользователей.

### 2. Сущности

#### Пользователь (User)
- **Описание**: Основная сущность для всех типов пользователей.
- **Поля**:
  - ID пользователя (уникальный)
  - Email
  - Номер телефона
  - Пароль (защищенный хэш)
  - Роль (например, "арендодатель", "клиент", "модератор")
  - Дата регистрации
  - `telegram_username` (опциональное поле для Telegram-идентификатора)

#### Арендодатель (Landlord)
- **Описание**: Подкласс пользователя, который предоставляет апартаменты в аренду.
- **Поля**:
  - ID арендодателя (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия
  - Профильная фотография

#### Клиент (Client)
- **Описание**: Подкласс пользователя, который арендует апартаменты.
- **Поля**:
  - ID клиента (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия

#### Модератор (Moderator)
- **Описание**: Подкласс пользователя, ответственный за управление контентом и бронированиями.
- **Поля**:
  - ID модератора (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия

#### Апартамент (Apartment)
- **Описание**: Сущность для описания арендуемых объектов.
- **Поля**:
  - ID апартамента (уникальный)
  - Название
  - Описание
  - Цена за ночь
  - Местоположение
  - Фото (ссылка на список фотографий)

#### Фото (Photo)
- **Описание**: Сущность для хранения изображений апартаментов.
- **Поля**:
  - ID фото (уникальный)
  - ID апартамента (ссылается на ID апартамента)
  - URL фотографии

#### Бронирование (Booking)
- **Описание**: Запись о предстоящей аренде апартаментов.
- **Поля**:
  - ID бронирования (уникальный)
  - ID арендодателя
  - ID клиента
  - ID апартамента
  - Дата начала аренды
  - Дата окончания аренды
  - Стоимость аренды
  - Статус бронирования

#### Оплата (Payment)
- **Описание**: Запись о финансовой транзакции.
- **Поля**:
  - ID платежа (уникальный)
  - ID бронирования
  - Сумма платежа
  - Дата и время оплаты
  - Статус оплаты

### Ключи и связи между сущностями

1. **Пользователь (User)**
   - **ID пользователя** (PK)
   - **Email**, **Номер телефона**
   - **Роль**: `Role` (enum), например, "арендодатель", "клиент", "модератор"

2. **Арендодатель (Landlord)**
   - **ID арендодателя** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**
   - **Профильная фотография**

3. **Клиент (Client)**
   - **ID клиента** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**

4. **Модератор (Moderator)**
   - **ID модератора** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**

5. **Апартамент (Apartment)**
   - **ID апартамента** (PK)
   - **Название**
   - **Описание**
   - **Цена за ночь**
   - **Местоположение**
   - **Список фотографий**: `List<Photo>`, где каждый элемент связан с ID апартамента через FK

6. **Фото (Photo)**
   - **ID фото** (PK)
   - **ID апартамента** (FK ссылается на ID апартамента в таблице Apartment)
   - **URL фотографии**

7. **Бронирование (Booking)**
   - **ID бронирования** (PK)
   - **ID арендодателя** (FK ссылается на ID арендодателя в таблице Landlord)
   - **ID клиента** (FK ссылается на ID клиента в таблице Client)
   - **ID апартамента** (FK ссылается на ID апартамента в таблице Apartment)
   - **Дата начала аренды**
   - **Дата окончания аренды**
   - **Стоимость аренды**
   - **Статус бронирования**

8. **Оплата (Payment)**
   - **ID платежа** (PK)
   - **ID бронирования** (FK ссылается на ID бронирования в таблице Booking)
   - **Сумма платежа**
   - **Дата и время оплаты**
   - **Статус оплаты**

### Логика авторизации

Для реализации логики авторизации можно использовать следующую структуру:

- **Пользователь** (`User`): хранит основные данные пользователя, включая email, номер телефона и пароль.
- **Роль** (`Role`): таблица с возможными ролями пользователей (арендодатель, клиент, модератор).
- **Аутентификация**: при входе проверяется соответствие email/номер телефона и хэша пароля. После успешной аутентификации определяется роль пользователя.
- **Авторизация**: в зависимости от роли пользователя предоставляются различные функции и доступы к системе.

### Технические детали

#### Backend
- **Стек технологий**: FastAPI + SQLAlchemy для Python 
- **База данных**: PostgreSQL с поддержкой асинхронных операций (asyncpg для Python).

#### Frontend
- **Технологии**: Использование Telegram bot API и веб-интерфейса для взаимодействия пользователей.
___________________________

Алембик. провел миграцию, добавил геополе location в модель Apartment. когда  пытаюсь наполнить данными таблицу запускаю python seed_create_user_landlord_client.py то ошибка  raise PydanticSchemaGenerationError(pydantic.errors.PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'geoalchemy2.types.Geography'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.
If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion. посмотри как предлагает документация решить https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.arbitrary_types_allowed


. ERROR tests/test_apartments.py::TestApartmentEndpoints::test_delete_apartmen
... t_not_found - sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) ne
... ar "POINT": syntax error
... 1 warning, 13 errors in 4.21s
The error you're encountering is related to the creation of a table with a `geography` column type, which SQLite does not support natively. SQLite supports `geometry` instead of 
`geography`. The issue appears when creating tables using SQLAlchemy and connecting through SQLite.

Here's how you can address this problem:

1. **Change Geography Type**: Modify your model or schema to use the appropriate geography type for SQLite, which is `GEOMETRY`.

2. **Ensure Proper Database Engine Configuration**: Make sure that your database engine configuration in SQLAlchemy points to a dialect that supports the correct spatial types (e.g., 
PostgreSQL for proper `geography` support).

3. **Adjust Test Environment**: If you're using an SQLite test environment, consider switching to another dialect like PostgreSQL for testing spatial data.

### Solution

#### Step 1: Change Geography Type
Update your model or schema definition in SQLAlchemy to use the correct type:

```python
from sqlalchemy import Column, Float, Integer, String, MetaData, Table
from sqlalchemy.dialects.sqlite import GEOMETRY as SQLiteGeometry

metadata = MetaData()

apartment_table = Table(
    'apartment',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),
    Column('description', String()),
    Column('price_per_night', Float, nullable=False),
    Column('address', String(255), nullable=False),
    # Use GEOMETRY instead of geography
    Column('location', SQLiteGeometry(geometry_type='POINT', srid=4326), nullable=False)
)
```

#### Step 2: Adjust Database Engine Configuration
Ensure your SQLAlchemy engine configuration uses the correct dialect for your database:

```python
from sqlalchemy import create_engine

# Example for PostgreSQL
engine = create_engine('postgresql://user:password@localhost/dbname')

# If you're using SQLite, ensure it's a proper connection string:
# engine = create_engine('sqlite:///test.db')
```

### Additional Considerations
- **Testing**: Ensure your tests are run against the correct database dialect. You might need to set up different test environments for PostgreSQL and SQLite.
- **Documentation**: Make sure that any documentation or setup instructions clearly state which spatial types are supported by each database.

By making these adjustments, you should be able to resolve the error related to unsupported `geography` type in SQLite and proceed with testing your application properly.
____________________________________

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely import wkb
from typing import List, Annotated
from app.schemas.photo import PhotoRead
from geoalchemy2.types import Geography
from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler, ValidationError, Field
from geoalchemy2.types import Geography
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue


class _GeographyPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        from geoalchemy2.elements import WKBElement

        def encode_geography(value):
            if isinstance(value, str):
                return value  # Assuming the string is already a valid WKT or WKB
            elif isinstance(value, WKBElement):
                return value.wkb.dumps()
            else:
                raise ValueError("Unsupported type for Geography")

        def decode_geography(value):
            if isinstance(value, bytes):
                return WKBElement(value, srid=4326)  # Assuming SRID is 4326
            elif isinstance(value, str):
                try:
                    import shapely.wkb
                    return shapely.wkb.loads(value)
                except Exception as e:
                    raise ValueError("Invalid WKT or WKB string") from e
            else:
                raise ValueError("Unsupported type for Geography")

        return core_schema.chain_schema([
            handler(Geography),
            core_schema.no_info_plain_validator_function(encode_geography),
            core_schema.plain_serializer_function_ser_schema(lambda v: v.wkb.dumps() if isinstance(v, WKBElement) else v),
            core_schema.no_info_custom_serializer_function_ser_schema(lambda v: v.dumps() if hasattr(v, 'dumps') else v),
        ], decoder=decode_geography)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {
            "title": "Geography",
            "type": "string",  # Assuming we're using a string representation (WKT or WKB)
            "example": "POINT(10.0 20.0)"
        }

# Create an Annotated type for Geography
GeographyPydantic = Annotated[Geography, _GeographyPydanticAnnotation]

___________________________________


todo 
in aparment key landlord. Ome to many.
