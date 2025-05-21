import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IntermediateBaselineService {

  constructor(private http: HttpClient) { }

  postData(value: any): Observable<any> {
    const url = environment.API_URL + "baseline/intermediate";

    return this.http.post(url, value);
  }

  transformIdToYear(id: number) {

    switch (id) {
      case 0:
        return 1945
      case 1:
        return 1969
      case 2:
        return 1979
      case 3:
        return 1989
      case 4:
        return 1999
      case 5:
        return 2010
      case 6:
        return 2050
      default:
        return 1999
    }
  }

  
  transformYearToId(id: number) {

    switch (id) {
      case 1945:
        return 0
      case 1969:
        return 1
      case 1979:
        return 2
      case 1989:
        return 3
      case 1999:
        return 4
      case 2010:
        return 5
      case 2050:
        return 6
      default:
        return 4
    }
  }

}