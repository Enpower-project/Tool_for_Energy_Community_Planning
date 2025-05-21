import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SessionStorageService {

  constructor() { }

  setObject(key: string, value: any): void {
    try {
      const jsonValue = JSON.stringify(value);
      sessionStorage.setItem(key, jsonValue);
    } catch (e) {
      console.error('Error guardando el objeto en sessionStorage', e);
    }
  }

  getObject<T>(key: string): T | null {
    try {
      const jsonValue = sessionStorage.getItem(key);
      if (jsonValue) {
        return JSON.parse(jsonValue) as T;
      }
      return null;
    } catch (e) {
      console.error('Error recuperando el objeto de sessionStorage', e);
      return null;
    }
  }

  removeObject(key: string): void {
    try {
      sessionStorage.removeItem(key);
    } catch (e) {
      console.error('Error eliminando el objeto de sessionStorage', e);
    }
  }
}