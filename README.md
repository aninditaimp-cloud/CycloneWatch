@'
# CycloneWatch

CycloneWatch is an integrated disaster management platform designed to connect affected individuals, their families, and rescue teams through a unified response system.

## Project Overview

The platform aims to support cyclone preparedness, emergency communication, SOS reporting, and location-based disaster impact assessment.

## Main Modules

### 1. Cyclone Alerts and Preparedness
Provides cyclone-related alerts and preparedness information to help users prepare before a disaster.

### 2. SOS and Safety Check-in
Allows users to share their location and request assistance. The system is designed to support emergency escalation when users do not respond to safety check-ins.

### 3. Satellite Impact Assessment
Uses historical satellite-derived flood data to assess whether an SOS location intersects a mapped flood zone.

The satellite module uses GeoJSON, Python, and spatial geometry processing. Its current reference dataset is from Sentinel Asia, dated 29 May 2021.

**Note:** Historical satellite data is used for prototype assessment, not live flood monitoring. A location outside mapped zones does not necessarily mean it is safe.

### 4. Family and Rescuer Communication
Designed to connect affected users, their family members, and rescue teams through a coordinated response system.

## Technology Stack

- Frontend: React, TypeScript, Vite
- Satellite processing: Python, GeoPandas, GeoJSON
- Version control: Git and GitHub

## Project Status

CycloneWatch is under development as a prototype disaster management platform.
'@ | Set-Content -Encoding utf8 README.md