import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import * as L from 'leaflet';
import { MapService } from '../../../services/map.service';

@Component({
  selector: 'app-address-selector',
  templateUrl: './address-selector.component.html',
  styleUrls: ['./address-selector.component.scss']
})
export class AddressSelectorComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();

  private map: any = null;
  private marker: any = null;
  public canSearch: boolean = false;
  public mapEdited: boolean = false;
  public searching: boolean = false;

  private icon: any = L.icon({
    iconUrl: './assets/icons/map-postion.svg',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });

  form: FormGroup = new FormGroup({});
  constructor(
    private formBuilder: FormBuilder,
    private mapService: MapService,
  ) { }

  ngOnInit() {
    this.initMap();
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      location: ["", Validators.required],
      locationOptions: [[]]
    });
    this.form.controls['location'].valueChanges.subscribe(() => { this.validateForm() })
  }

  private validateForm() {
    if (this.form.controls['location'].value) {
      this.mapEdited ? (this.mapEdited = false, this.canSearch = false) : this.canSearch = true
    } else {
      this.canSearch = false;
    }
  }

  private initMap(): void {
    this.map = L.map('map', {
      center: [43.3639000, -2.5354000],
      zoom: 12,
    });

    const tiles = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution:
          '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }
    );

    tiles.addTo(this.map);

    this.map.on('click', (e: L.LeafletMouseEvent) => {

      var lat = e.latlng.lat;
      var lng = e.latlng.lng;
      this.createMarker(lat, lng)

      this.mapService.getLocationInfo(lat, lng).subscribe({
        next: (data: any) => {
          this.mapEdited = true;
          this.form.controls['location'].setValue(data.display_name);
        }, error: (err: any) => {
          console.error(err.message)
        }
      })
    })
  }

  private createMarker(lat: number, lng: number) {
    if (this.marker) {
      this.map.removeLayer(this.marker);
    }

    this.marker = L.marker([lat, lng], { icon: this.icon }).addTo(this.map);
  }

  public searchStreet() {
    if (!this.searching) {
      this.searching = true;
      this.canSearch = false;
      if (this.form.controls['location'].value) {
        this.mapService.getMapPosition(this.form.controls['location'].value ?? "").subscribe({
          next: (data: any) => {
            this.searching = false;
            if (data && data.length > 0) {
              const latlng = L.latLng(data[0].lat, data[0].lon);
              this.createMarker(data[0].lat, data[0].lon)
              this.map.panTo(latlng);
              this.form.controls['location'].setValue(data[0].display_name);
            } else {
              console.error('No se encontró ninguna ubicación para la calle ingresada.');
            }
          }, error: (err: any) => {
            this.searching = false;
            console.error(err.message)
          }
        })
      } else {
        this.searching = false;
      }
    }
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    this.next.emit(this.marker);
  }


}
