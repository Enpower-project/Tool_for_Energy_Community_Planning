import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FindCommunityService {

  constructor(private http: HttpClient) { }

  getCommunityList(): Observable<any> {

    const url = environment.API_URL + "context";

    return this.http.get(url);
  }

  getCommunityById(id: number): Observable<any> {

    const url = environment.API_URL + "context/" + id;

    return this.http.get(url);
  }

  getCommunityByIdComplete(id: number): Observable<any> {

    const url = environment.API_URL + "context/data/" + id;

    return this.http.get(url);
  }

  getCommunityAlternatives(id: number): Observable<any> {

    const url = environment.API_URL + "context/" + id + "/alternatives";

    return this.http.get(url);
  }

  deleteCommunity(id: number): Observable<any> {

    const url = environment.API_URL + "context/" + id;

    return this.http.delete(url);
  }

}