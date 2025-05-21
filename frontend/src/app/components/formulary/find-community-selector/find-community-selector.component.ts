import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import L, { LeafletEvent } from 'leaflet';
import 'leaflet.markercluster';
import { MapService } from '../../../services/map.service';
import { CardInfo } from '../../../data/types';
import { FindCommunityService } from '../../../services/find-community.service';
import { WKTService } from '../../../services/WKT.service';

@Component({
  selector: 'app-find-community-selector',
  templateUrl: './find-community-selector.component.html',
  styleUrls: ['./find-community-selector.component.scss']
})
export class FindCommunitySelectorComponent implements OnInit {

  @Input() communityList: any;
  @Input() loading: boolean = false;

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Output() createNewCommunity = new EventEmitter();

  private map: any = null;
  private markers: any = [];
  public showCommunityList: boolean = false;
  public mapEdited: boolean = false;
  public searching: boolean = false;
  public loadingCommunity: boolean = true;

  public cardList: CardInfo[] = [];
  public mapLoading: boolean = true;

  private icon: any = L.icon({
    iconUrl: './assets/icons/community.svg',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });

  form: FormGroup = new FormGroup({});
  constructor(
    private formBuilder: FormBuilder,
    private mapService: MapService,
    private findCommunityService: FindCommunityService,
    private WKTservice: WKTService
  ) { }

  ngOnInit() {
    this.setForm();
    this.initMap();
    if (!this.communityList)
      this.getCommunityList();
    else
      this.addClusterMarkers();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      location: [""],
      community: ["", Validators.required],
    });
  }

  private initMap(): void {
    this.map = L.map('map_find', {
      center: [40.416775, -3.703790],
      zoom: 6,
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
    
  }

  private addClusterMarkers(): void {

    const markerList = [];

    //recorrer
    const markers = L.markerClusterGroup({
      maxClusterRadius: 100,
      removeOutsideVisibleBounds: true,
      zoomToBoundsOnClick: false
    });

    this.communityList.forEach((community: any) => {

      const coords = community?.geom?.replace('POINT (', '')?.replace(')', '')?.split(' ')
      if (coords.length === 2) {
        let point = L.marker([coords[1], coords[0]], { icon: this.icon });
        (point as any).info = community.id;
        point.on('click', () => {
          this.selectCommunityPoint(community);
        });
        markers.addLayer(point);
      }
    });

    markerList.push(markers)

    this.markers.push(markerList)
    markers.on('clusterclick', (a: LeafletEvent) => {
      this.onClusterClick(a);
    });

    this.map.addLayer(markers);
    this.mapLoading = false;
  }

  private selectCommunityPoint(community: any) {
    this.showCommunityList = true;
    this.cardList = [{
      iconName: 'community.svg',
      title: community.name,
      description: community.description,
      infoIcon: false,
      id: community.id
    }];
  }

  private onClusterClick(a: any): void {
    this.showCommunityList = true;
    this.generateCardList(a.layer.getAllChildMarkers());
  }

  private generateCardList(markList: any) {
    this.cardList = []
    markList.forEach((mark: any) => {
      const community = this.communityList.find((commumity: any) => commumity.id === mark.info);
      if (community) {
        this.cardList.push(
          {
            iconName: 'community.svg',
            title: community.name,
            description: community.description,
            infoIcon: false,
            id: community.id
          }
        )
      }
    });
  }

  public searchStreet() {
    if (!this.searching) {
      this.searching = true;
      if (this.form.controls['location'].value) {
        this.mapService.getMapPosition(this.form.controls['location'].value ?? "").subscribe({
          next: (data: any) => {
            this.searching = false;
            if (data && data.length > 0) {
              const latlng = L.latLng(data[0].lat, data[0].lon);
              this.map.flyTo(latlng);
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
    this.loading = true;
    this.getCountry(this.communityList.filter((community: any) => community.id == this.form.controls['community'].value.id));

  }

  public createYourCommunity() {
    this.createNewCommunity.emit();
  }

  selectCommunity(card: CardInfo) {
    this.form.controls['community'].setValue(card)
  }


  public getCommunityList() {
    this.loadingCommunity = true;
    this.loadingCommunity = false;
    this.mapLoading = true;

    this.findCommunityService.getCommunityList().subscribe({
      next: (data: any) => {
        this.communityList = data;
        this.addClusterMarkers();
      }, error: (err: any) => {
        this.mapLoading = false;
        this.loadingCommunity = false;
        console.error(err.message)
      }
    })
  }

  private getCountry(communnity: any) {
    const coords: any = this.WKTservice.WktToCoords("POINT ", communnity[0].geom);
    this.mapService.getLocationInfo(coords[1], coords[0]).subscribe({
      next: (data: any) => {
        this.next.emit({
          card: this.form.controls['community'].value,
          country: data.address.country_code?.toUpperCase(),
          author: communnity[0]?.author
        }
        );
      }, error: (err: any) => {
        console.error(err.message)
      }
    })
  }

}
