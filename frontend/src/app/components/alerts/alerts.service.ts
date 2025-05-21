import { Injectable } from '@angular/core';
import { Subject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AlertsService {

  private subject = new Subject<any>();

  info(message: string): void {
    this.subject.next(
      {
        message: message,
        type: ALERT_TYPE.INFO
      });
  }

  error(message: string): void {
    this.subject.next(
      {
        message: message,
        type: ALERT_TYPE.ERROR
      });
  }

  getAlert(): Observable<any> {
    return this.subject.asObservable();
  }
}

export enum ALERT_TYPE {
  INFO, ERROR
}