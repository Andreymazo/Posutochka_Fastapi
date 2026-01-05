### Added
- New Balance model to track earnings from bookings with full CRUD API endpoints
- New Review model for rating system (1-5 stars) with booking, landlord, and client relationships
- Pydantic schemas for Balance and Review (Create, Read, Update)
- Complete test coverage for Balance and Review models including schema validation and API endpoints
- API routers for /balances and /reviews with filtering capabilities

### Fixed
- Balance model now includes required booking_id foreign key for proper relationship with bookings
