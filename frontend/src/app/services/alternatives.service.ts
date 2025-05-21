import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AlternativesService {

  constructor(private http: HttpClient) { }

  postAlternativeConfig(value: any): Observable<any> {
    const url = environment.API_URL + "alternatives/technologies";
    return this.http.post(url, value);
  }

}
