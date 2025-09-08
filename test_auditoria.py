#!/usr/bin/env python
"""
Script para probar la funcionalidad de auditoría
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/api"
EMAIL_PRUEBA = "admin@example.com"
PASSWORD_PRUEBA = "admin123"


def mostrar_seccion(titulo):
    """Mostrar una sección del test"""
    print(f"\n{'='*50}")
    print(f" {titulo}")
    print(f"{'='*50}")


def test_login_exitoso():
    """Probar login exitoso"""
    mostrar_seccion("TEST: LOGIN EXITOSO")
    
    url = f"{BASE_URL}/token/"
    data = {
        "email": EMAIL_PRUEBA,
        "password": PASSWORD_PRUEBA
    }
    
    print(f"Enviando POST a {url}")
    print(f"Datos: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login exitoso")
            print(f"Token obtenido: {result.get('access', '')[:50]}...")
            return result.get('access')
        else:
            print("❌ Login falló")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_login_fallido():
    """Probar login con credenciales incorrectas"""
    mostrar_seccion("TEST: LOGIN FALLIDO")
    
    url = f"{BASE_URL}/token/"
    data = {
        "email": EMAIL_PRUEBA,
        "password": "password_incorrecto"
    }
    
    print(f"Enviando POST a {url}")
    print(f"Datos: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Login falló como esperado (esto genera un log de auditoría)")
        else:
            print("❌ Comportamiento inesperado")
            
        print(f"Respuesta: {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")


def test_crear_usuario(token):
    """Probar creación de usuario"""
    if not token:
        print("❌ No hay token disponible")
        return
        
    mostrar_seccion("TEST: CREAR USUARIO")
    
    url = f"{BASE_URL}/usuarios/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "email": "nuevo_usuario@example.com",
        "password": "password123",
        "first_name": "Nuevo",
        "last_name": "Usuario"
    }
    
    print(f"Enviando POST a {url}")
    print(f"Headers: {headers}")
    print(f"Datos: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Usuario creado exitosamente")
            print(f"ID del usuario: {result.get('id')}")
            return result.get('id')
        else:
            print("❌ Error creando usuario")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_actualizar_usuario(token, user_id):
    """Probar actualización de usuario"""
    if not token or not user_id:
        print("❌ No hay token o ID de usuario disponible")
        return
        
    mostrar_seccion("TEST: ACTUALIZAR USUARIO")
    
    url = f"{BASE_URL}/usuarios/{user_id}/"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "first_name": "Nombre Actualizado",
        "last_name": "Apellido Actualizado"
    }
    
    print(f"Enviando PATCH a {url}")
    print(f"Headers: {headers}")
    print(f"Datos: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.patch(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Usuario actualizado exitosamente")
        else:
            print("❌ Error actualizando usuario")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")


def test_consultar_logs_auditoria(token):
    """Consultar logs de auditoría"""
    if not token:
        print("❌ No hay token disponible")
        return
        
    mostrar_seccion("TEST: CONSULTAR LOGS DE AUDITORÍA")
    
    url = f"{BASE_URL}/auditoria/logs/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Enviando GET a {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Logs obtenidos exitosamente")
            print(f"Total de logs: {result.get('count', 0)}")
            
            # Mostrar los últimos 5 logs
            logs = result.get('results', [])[:5]
            print("\nÚltimos 5 logs:")
            for i, log in enumerate(logs, 1):
                print(f"{i}. {log.get('timestamp')} - {log.get('usuario_email')} - {log.get('accion_display')}")
                
        else:
            print("❌ Error obteniendo logs")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")


def test_estadisticas_auditoria(token):
    """Consultar estadísticas de auditoría"""
    if not token:
        print("❌ No hay token disponible")
        return
        
    mostrar_seccion("TEST: ESTADÍSTICAS DE AUDITORÍA")
    
    url = f"{BASE_URL}/auditoria/logs/estadisticas/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Enviando GET a {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Estadísticas obtenidas exitosamente")
            print(f"Total de eventos: {result.get('total_eventos', 0)}")
            print(f"Período: {result.get('periodo_dias', 0)} días")
            
            print("\nEventos por acción:")
            for accion in result.get('estadisticas_por_accion', []):
                print(f"  {accion.get('accion')}: {accion.get('total')}")
                
        else:
            print("❌ Error obteniendo estadísticas")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")


def main():
    """Función principal para ejecutar todos los tests"""
    print("🚀 INICIANDO PRUEBAS DE AUDITORÍA")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    
    # Test 1: Login fallido (genera log de auditoría)
    test_login_fallido()
    
    # Test 2: Login exitoso
    token = test_login_exitoso()
    
    if token:
        # Test 3: Crear usuario (genera log de auditoría)
        user_id = test_crear_usuario(token)
        
        # Test 4: Actualizar usuario (genera log de auditoría)
        if user_id:
            test_actualizar_usuario(token, user_id)
        
        # Test 5: Consultar logs de auditoría
        test_consultar_logs_auditoria(token)
        
        # Test 6: Consultar estadísticas
        test_estadisticas_auditoria(token)
    
    mostrar_seccion("PRUEBAS COMPLETADAS")
    print("✅ Todas las pruebas han sido ejecutadas")
    print("📋 Revisa los logs de auditoría en el admin de Django o mediante la API")


if __name__ == "__main__":
    main()
