import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MapService {

  constructor(private http: HttpClient) { }

  /**
   * transform coords to the name of the street 
   *
   * @param {number} lat
   * @param {number} lng
   * @returns {Observable<any>}
   */
  getLocationInfo(lat: number, lng: number): Observable<any> {
    const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`;
    return this.http.get(url);
  }

  /**
    * transform street name to coords
   *
   * @param {string} location
   * @returns {*}
   */
  getMapPosition(location: string) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}`;
    return this.http.get(url);
  }

}
