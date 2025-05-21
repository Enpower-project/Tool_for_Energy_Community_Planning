import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BasicBaselineService {

  constructor(private http: HttpClient) { }

  postData(value: any): Observable<any> {
    const url = environment.API_URL + "baseline/basic";
    return this.http.post(url, value);
  }

  getBuildingUsesList(): Observable<any> {
    const url = environment.API_URL + "catalogue/building-use";
    return this.http.get(url);
  }

  getCommonProfileList(): Observable<any> {
    const url = environment.API_URL + "catalogue/common-profile";
    return this.http.get(url);
  }

  postSaveCommunity(data: any): Observable<any> {
    const url = environment.API_URL + "context";
    return this.http.post(url, data);
  }

  changeCommunityName(id: number, newName: string): Observable<any> {
    const url = environment.API_URL + "context/" + id + `?name=${newName}`;
    return this.http.put(url, null);
  }

}