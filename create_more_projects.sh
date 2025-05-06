#\!/bin/bash
# Create more structured projects for other areas

# Create Error Handling project
gh project create --title "Error Handling Framework (Repository)" --owner arockwell
gh project edit 11 --owner arockwell --readme "# Error Handling Framework

This project tracks standardizing error handling across the local_newsifier application.

## Components:
- CRUD layer error handling
- Service layer error handling
- API endpoint error handling
- Pipeline error recovery
- Decorator-based error handling
- Specialized database error handlers"

# Add error handling issues
ERROR_PROJECT="Error Handling Framework (Repository)"
ERROR_ISSUES=(171 170 169 118 80 79 78 77 75 74)

for ISSUE in "${ERROR_ISSUES[@]}"; do
  echo "Adding issue #$ISSUE to $ERROR_PROJECT"
  gh issue edit "$ISSUE" --add-project "$ERROR_PROJECT"
done

# Create DI project
gh project create --title "Dependency Injection (Repository)" --owner arockwell
gh project edit 12 --owner arockwell --readme "# Dependency Injection

This project tracks the migration to fastapi-injectable and dependency injection improvements.

## Components:
- fastapi-injectable migration
- Provider functions
- Testing support
- API dependency functions
- Legacy DIContainer removal"

# Add DI issues
DI_PROJECT="Dependency Injection (Repository)"
DI_ISSUES=(200 143 119 122 141 151 202 203 204 205 206 207 208 211 212)

for ISSUE in "${DI_ISSUES[@]}"; do
  echo "Adding issue #$ISSUE to $DI_PROJECT"
  gh issue edit "$ISSUE" --add-project "$DI_PROJECT"
done
