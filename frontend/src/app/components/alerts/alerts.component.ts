import { Component, OnInit } from '@angular/core';
import { AlertsService } from './alerts.service';

@Component({
  selector: 'alertups',
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.scss']
})
export class AlertsComponent implements OnInit {

  public message: string = '';
  public type: any;

  constructor(private alertsService: AlertsService) { }

  ngOnInit(): void {
    this.alertsService.getAlert().subscribe(alerta => {
      this.type = alerta.type;
      this.message = alerta.message;
    });
  }

  closeModal(): void {
    this.message = '';
    this.type = '';
  }
}
