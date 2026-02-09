## REMOVED Requirements

### Requirement: Configure PostgreSQL connection
**Reason**: Database configuration must be environment-only per CLAUDE.md policy. UI and API endpoints conflict with security requirements.
**Migration**: Remove all database configuration UI components and API endpoints. Database settings remain in server/.env file only.

### Requirement: Configure Redis connection
**Reason**: Database configuration must be environment-only per CLAUDE.md policy. UI and API endpoints conflict with security requirements.
**Migration**: Remove all database configuration UI components and API endpoints. Redis settings remain in server/.env file only.

### Requirement: Database configuration validation
**Reason**: No longer needed as database configuration is environment-only.
**Migration**: Remove validation endpoints. Environment variable validation happens at application startup.

### Requirement: Non-admin access restriction
**Reason**: No longer needed as database configuration endpoints are removed entirely.
**Migration**: Remove all database configuration access control logic.
