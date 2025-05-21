import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import * as L from 'leaflet';
import { MapStyleService } from '../../../../services/map-style.service';
import { OverpassService } from '../../../../services/overpass.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-building-advanced',
  templateUrl: './building-advanced.component.html',
  styleUrls: ['./building-advanced.component.scss', '../../../basic-components/dropdown/dropdown.component.scss', '../../../basic-components/alert-messages/alert-messages.component.scss']
})
export class BuildingAdvancedComponent implements OnInit {

  private buildingType = 2;
  private comunnityProfile = 2;
  private defaultNumMembers = 3;
  private defaultParticipants = 4;
  private defaultNumDelings = 4;
  public year: number = 3;

  @Input() active: boolean = false;
  @Input() building: any;
  @Input() buildingUseList: any;
  @Input() commonProfileList: any;
  @Input() position: number = 0;
  @Input() valid: boolean = false;
  @Input() buildingList: any;
  @Input() canDeleteBuilding: boolean = true;
  @Input() markerMapPosition: any;
  @Output() save = new EventEmitter();
  @Output() delete = new EventEmitter();
  @Output() saveName = new EventEmitter();
  private map: any = null;
  private geoJsonLayer?: L.GeoJSON;
  public marker: any;
  public layerPosition: any;
  public mapLoading: boolean = false;
  public selectedProperties: any;
  private lastLayer: any;
  public selectedBUildings: any = [];
  public selectedBuilding: any;
  public changing: boolean = false;
  public commonProfileListName?: string[];
  public buildingUseListName?: string[];
  public savedBuilding: any;
  public isEditNameModalOpen: boolean = false;
  public savedLayer: any;
  public blockedBuildingList: any;
  public isDeleteModalOpen: boolean = false;

  formAdvanced: FormGroup = new FormGroup({});

  constructor(
    private overpassService: OverpassService,
    private mapStyleService: MapStyleService,
    private formBuilder: FormBuilder,
    private translateService: TranslateService
  ) { }

  ngOnInit() {
    this.buildingUseListName = this.buildingUseList.map((pro: any) => pro.name_translate);;
    this.commonProfileListName = this.commonProfileList.map((pro: any) => pro.name_translate);
    this.setForm();
    if (this.building) {
      this.valid = true;
      this.loadBuilding();
    }
    if (this.active) {
      this.initMap();
    }
  }

  public activeIt() {
    this.active = !this.active;
    if (this.active) {
      this.changing = true;
      setTimeout(() => {
        this.buildingUseListName = this.buildingUseList.map((pro: any) => pro.name_translate);;
        this.commonProfileListName = this.commonProfileList.map((pro: any) => pro.name_translate);
        this.initMap();
        this.changing = false;
      }, 100);
    }
  }

  //#region Form

  public setForm() {
    this.formAdvanced = this.formBuilder.group({
      buildingName: ["building " + (this.position + 1), Validators.required],
      buildingId: ["", Validators.required],
      buildingType: [this.buildingType, Validators.required],
      comunnityProfile: [this.comunnityProfile, Validators.required],
      buildingYear: [this.year, Validators.required],
      dwellings: [this.defaultNumDelings],
      occupants: [this.defaultParticipants],
      members: [this.defaultNumMembers, Validators.required],
    });
  }

  public loadBuilding() {
    this.formAdvanced.controls['buildingName'].setValue(this.building.buildingName);
    this.formAdvanced.controls['buildingId'].setValue(this.building.buildingId);
    this.formAdvanced.controls['buildingType'].setValue(this.building.buildingType);
    this.formAdvanced.controls['comunnityProfile'].setValue(this.building.comunnityProfile);
    this.formAdvanced.controls['buildingYear'].setValue(this.building.buildingYear);
    this.formAdvanced.controls['dwellings'].setValue(this.building.dwellings);
    this.formAdvanced.controls['occupants'].setValue(this.building.occupants);
    this.formAdvanced.controls['members'].setValue(this.building.members);
  }

  //#endregion

  //#region MAP
  public initMap(): void {
    this.map = L.map('map-advanced-' + this.position, {
      center: [41.6525, -4.7245],
      zoom: 16,
    });

    const tiles = L.tileLayer(
      'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {
        attribution:
          '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        minZoom: 16
      }
    );

    if (this.markerMapPosition) {
      this.map.setView(this.markerMapPosition.getLatLng(), 16);
    }

    tiles.addTo(this.map);
    if (this.marker) {
      this.map.setView(this.marker.getLatLng(), 16);
    }

    if (this.layerPosition) {
      this.map.setView(this.layerPosition.getCenter(), 16);
    }
    this.loadBuildings();

    this.map.on('moveend', () => this.loadBuildings());
    this.map.on('zoomend', () => this.loadBuildings());
  }

  loadBuildings(): void {
    this.mapLoading = true;
    const bounds = this.map.getBounds();
    this.overpassService.getBuildingsInBoundary(bounds.getSouth(), bounds.getWest(), bounds.getNorth(), bounds.getEast()).subscribe({
      next: (data: any) => {
        if (this.geoJsonLayer) {
          this.geoJsonLayer.remove();
        }

        this.geoJsonLayer = L.geoJSON(this.overpassService.convertOsmToGeoJson(data), {
          onEachFeature: (feature, layer) => {

            if (this.selectedBUildings?.find((build: any) => build?.properties?.properties?.id === feature.properties.id)) {
              if (this.selectedBUildings[this.selectedBuilding]?.properties?.properties?.id !== feature.properties.id) {
                (layer as any).setStyle(this.mapStyleService.getBuildingColor('disabled'));
              }
            }

            if (this.selectedProperties && this.selectedProperties.properties.id === feature.properties.id) {
              this.selectedProperties = feature;
              this.lastLayer = layer;
              (layer as any).setStyle(this.mapStyleService.getBuildingColor('selected'));
            }

            layer.on('click', () => {
              this.clickLayer(feature, layer)
            });

          },
          style: () => (this.mapStyleService.getBuildingColor('basic'))
        }).addTo(this.map);

        if (this.building && !this.layerPosition) {
          this.savedLayer = L.geoJSON(this.building.buildingId).addTo(this.map);
          (this.savedLayer as any).setStyle(this.mapStyleService.getBuildingColor('selected'));
        }

        if (this.buildingList) {
          if (this.blockedBuildingList && this.blockedBuildingList.length > 0) {
            this.blockedBuildingList.map((layert: any) => layert.remove());
          }

          this.blockedBuildingList = [];
          for (let index = 0; index < this.buildingList.length; index++) {
            if (this.buildingList[index] && index !== this.position && this.buildingList[index].buildingId) {
              this.blockBuilding(this.buildingList[index].buildingId)
            }
          }
        }

        this.mapLoading = false;
      }, error: (err: any) => {
        this.mapLoading = false;
        console.error(err.message)
      }
    });

  }

  private clickLayer(properties: any, layer: L.Layer): void {

    if (this.savedLayer) {
      this.map.removeLayer(this.savedLayer);
    }

    if (this.selectedBUildings[this.selectedBuilding]?.properties?.properties?.id === properties.properties.id || !this.selectedBUildings?.find((build: any) => build?.properties?.properties?.id === properties.properties.id)) {
      this.deleteLayerColor();
      this.selectedProperties = properties;
      this.lastLayer = layer;
      this.formAdvanced.controls["buildingId"].setValue(properties);
      this.layerPosition = (layer as L.Polygon).getBounds();
      (layer as any).setStyle(this.mapStyleService.getBuildingColor('selected'));
    }
  }

  private blockBuilding(properties: any) {

    this.blockedBuildingList.push(L.geoJSON(properties).addTo(this.map));
    this.blockedBuildingList[this.blockedBuildingList.length - 1].setStyle(this.mapStyleService.getBuildingColor('disabled'));

  }

  private deleteLayerColor() {
    if (this.lastLayer) {
      (this.lastLayer as any).setStyle(this.mapStyleService.getBuildingColor('basic'))
    }
  }

  //#endregion

  //#region year configuration

  public setYear(year?: number) {

    if (year !== undefined) {
      this.year = year
      this.formAdvanced.controls["buildingYear"].setValue(this.year);
    }

    this.getYear();
  }

  public getYear() {
    let value;
    value = this.translateService.instant("BASELINE.ADVANCED.SLIDER." + (this.year + 1))
    return value;
  }

  //#endregion

  public saveIt() {
    this.savedBuilding = {
      buildingName: this.formAdvanced.controls["buildingName"].value,
      buildingId: this.formAdvanced.controls["buildingId"].value,
      buildingType: this.formAdvanced.controls["buildingType"].value,
      comunnityProfile: this.formAdvanced.controls["comunnityProfile"].value,
      buildingYear: this.formAdvanced.controls["buildingYear"].value,
      dwellings: this.formAdvanced.controls["dwellings"].value,
      occupants: this.formAdvanced.controls["occupants"].value,
      members: this.formAdvanced.controls["members"].value
    }

    if (this.formAdvanced.valid) {
      this.valid = true;
      this.active = false;
      this.save.next(this.savedBuilding);
    }
  }

  public deleteBuilding() {
    this.isDeleteModalOpen = false;
    this.active = false;
    this.delete.emit();
  }

  //#region Cambiar el nombre

  public closeEditNameModal() {
    this.isEditNameModalOpen = false;
  }

  public saveNewNameCommunity(name: string) {
    if (name) {
      this.formAdvanced.controls['buildingName'].setValue(name);
      this.closeEditNameModal();
      if (this.valid) {
        this.saveName.next(name);
      }
    }
  }

  public getName() {
    return this.formAdvanced.controls['buildingName'].value;
  }

  //#endregion

}
