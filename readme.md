# Tadanarchy

## The link to the project

```bash
https://scar-16-olek.tail516b3d.ts.net/app
```

## Overview

The City Eye was created to help citizens of Krakow get information about the possible outages, floods, road works and other city disasters. Additionally, the forum option is implemented, allowing users to add details while the problem exists, incorporating the feeling of “Same thing for me!” to create the sense of community.

## Key features + demo
- **Crisis view of the whole Krakow app with all existing issues**
  
<img width="2523" height="1181" alt="image" src="https://github.com/user-attachments/assets/b15c8ab6-f9ef-4e2d-93ea-51b1c1386be5" />

- **Possibility to filter the map by the specific types of disasters, such as:** no heating/hot water; no water; no power; flooding; tram/bus problems; street blocked/traffic; danger
- **Possibility to see users' messages with respect to historical context**
  
<img width="646" height="1177" alt="image" src="https://github.com/user-attachments/assets/18d751ba-e619-417b-88cf-2934c77f1e2a" />

## Installation guide

```bash
git clone https://github.com/Al3xrunner/TadAnarchy2026.git
```
create .venv env in root directory and activate
```bash
pip install -r backend/requirements.txt
```
To activate the frontend:

```bash
cd frontend
npm install
npm install leaflet react-leaflet react-router
```
To start the programm:

```bash
cd frontend
npm run build
cd ..\backend
```
activate .venv

```bash
python -m load_data
python -m app
```
