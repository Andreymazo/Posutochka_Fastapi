from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Table, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geography
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(Enum('landlord', 'client'), nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    telegram_username: Mapped[str] = mapped_column(String(32)) 
    # Relationship - One-to-One
    landlord: Mapped["Landlord"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    client: Mapped["Client"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
  

class Landlord(Base):
    __tablename__ = 'landlord'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True , nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped["User"] = relationship(back_populates="landlord")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="landlord")
    

class Client(Base):
    __tablename__ = 'client'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    user: Mapped["User"] = relationship(back_populates="client", )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="client")

class Apartment(Base):
    __tablename__ = 'apartment'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price_per_night: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Geography] = mapped_column(Geography(geometry_type='POINT', srid=4326))

    photos: Mapped[list["Photo"]] = relationship(back_populates="apartment")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="apartment")

    def __repr__(self):
        return f"Apartment(id={self.id}, name='{self.name}', " \
               f"description='{self.description}', " \
               f"price_per_night={self.price_per_night}, adress='{self.address}')"


class Photo(Base):
    __tablename__ = 'photo'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey('apartment.id'), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    apartment: Mapped["Apartment"] = relationship(back_populates="photos")

class Booking(Base):
    __tablename__ = 'booking'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    booking_status: Mapped[str] = mapped_column(Enum('pending', 'confirmed', 'cancelled'), nullable=False)
    # Ключи
    landlord_id: Mapped[int] = mapped_column(ForeignKey('landlord.id'), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey('client.id'), nullable=False)
    apartment_id: Mapped[int] = mapped_column(ForeignKey('apartment.id'), nullable=False)
  
    # Обратные связи
    landlord: Mapped["Landlord"] = relationship(back_populates="bookings")
    client: Mapped["Client"] = relationship(back_populates="bookings")
    apartment: Mapped["Apartment"] = relationship(back_populates="bookings")
    
    # Связь с платежами
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking", uselist=True)


class Payment(Base):
    __tablename__ = 'payment'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey('booking.id'), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payment_status: Mapped[str] = mapped_column(Enum('paid', 'pending', 'failed'), nullable=False)
    # Обратная связь
    booking: Mapped["Booking"] = relationship(back_populates="payments")
    
