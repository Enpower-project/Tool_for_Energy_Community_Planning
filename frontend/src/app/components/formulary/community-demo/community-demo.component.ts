import { Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { CardInfo, cardArrayModule } from '../../../data/types';
import { TranslateService } from '@ngx-translate/core';
import { KeycloakService } from 'keycloak-angular';
import { SessionStorageService } from '../../../services/session-storage.service';
import * as L from 'leaflet';
import { WKTService } from '../../../services/WKT.service';
import { OurCommunityComponent } from '../our-community/our-community.component';

@Component({
  selector: 'app-community-demo',
  templateUrl: './community-demo.component.html',
  styleUrls: ['./community-demo.component.scss']
})
export class CommunityDemoComponent implements OnInit {

  @Output() back = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Output() generateComunnity = new EventEmitter();
  @Input() editable: boolean = true;
  @Input() coords: any = [43.3639000, -2.5354000];
  @Input() isAdvanced: boolean = false;
  @Input() descriptionText?: string;
  @Input() descriptionIcon?: string;
  @Input() buttonSave: boolean = true;
  @Input() isMemberModalOpen: boolean = false;
  @Input() isEditNameModalOpen: boolean = false;
  @Input() isSelectingLevelModalOpen: boolean = false;
  @Input() selectAlternatives: boolean = true;
  @Input() position: any;
  @Input() communityName?: string;
  @Input() baselineData: any;
  @Input() buildingIconName: string = "Multi family house.svg";
  @Input() lockedCreateAlternative: boolean = false;
  @Input() LoadingCreateCommunity: boolean = false;
  @Input() kpi: any;
  @Input() cardArray?: CardInfo[];
  @Input() disableCompareBTN: boolean = true;
  @Input() disableNewAlterBTN: boolean = true;

  public marker: any;
  public polygons: any[] = [];
  public polygonsLayer: any;


  private icon: any = L.icon({
    iconUrl: './assets/icons/map-postion.svg',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });

  private map: any = null;

  @ViewChild('scrollContainer', { static: true }) scrollContainer!: ElementRef;

  constructor(
    private translate: TranslateService,
    private readonly keycloak: KeycloakService,
    private sessionStorage: SessionStorageService,
    private WKTService: WKTService,
  ) { }

  ngOnInit() {
    this.initMap();
    if (!this.communityName)
      this.communityName = this.baselineData.baseline.name ?? ((this.position ?? "Community") + " 01");
    this.position = this.baselineData.baseline.description ?? this.position;
    this.loadKPI();
  }

  private loadKPI(){
    this.kpi=  {
      value: this.convertEnergy(this.sum(this.baselineData?.kpis['total_primary_energy_[kWh]'].value)).value,
      unit: this.convertEnergy(this.sum(this.baselineData?.kpis['total_primary_energy_[kWh]'].value)).unit,
      kpi: this.baselineData?.kpis['total_primary_energy_[kWh]'].value,
      card: this.translate.instant('KPI.PRIMARY_ENERGY_CONSUMPTION.CARD')
        .replace("{total_primary_energy_intensity}", this.baselineData?.kpis['total_primary_energy_intensity'].value.toFixed(2))
        .replace("{XXX higher/lower/equal}", this.compareValues(this.baselineData?.kpis['total_primary_energy_intensity'].value, this.baselineData?.kpis['national_average_total_primary_energy_intensity'].value))
        .replace("{national_average_total_primary_energy_intensity}", this.baselineData?.kpis['national_average_total_primary_energy_intensity'].value.toFixed(2)),
      messages: [this.sum(this.baselineData?.kpis['EquivalentTVHours_[h]'].value), this.sum(this.baselineData?.kpis['PizzaConsumptionComparison_[pizza]'].value), this.sum(this.baselineData?.kpis['ElectricCarChargingEstimation_[charges]'].value)]
    }
  }

  private sum(value: number[]) {
    return value.reduce((acumulador: number, valorActual: number) => {
      return acumulador + valorActual;
    }, 0)
  }

  private compareValues(value1: number, value2: number) {
    if (value1 > value2) {
      return this.translate.instant('KPI.HIGHER')
    } else if (value1 < value2) {
      return this.translate.instant('KPI.LOWER')
    }
    else {
      return this.translate.instant('KPI.EQUAL')
    }
  }

  private convertEnergy(value: number, decimals: number = 2) {
    if (value >= 1_000_000) {
      return {
        value: (value / 1_000_000).toFixed(decimals),
        unit: 'GWh'
      };
    } else if (value >= 1000) {
      return {
        value: (value / 1000).toFixed(decimals),
        unit: 'MWh'
      };
    } else {
      return {
        value: value.toFixed(decimals),
        unit: 'kWh'
      };
    }
  }

  public goBack() {
    this.back.emit()
  }

  public closeIt() {
    this.close.emit()
  }

  public goNext() {
    this.next.emit(this.baselineData);
  }

  public generateNewCommunity() {
    this.generateComunnity.emit();
  }

  public openMemberModal() {
    this.isMemberModalOpen = true;
  }

  public closeMemberModal() {
    this.isMemberModalOpen = false;
  }

  public openEditNameModal() {
    this.isEditNameModalOpen = true;;
  }

  public closeEditNameModal() {
    this.isEditNameModalOpen = false;;
  }

  public saveNewNameCommunity(newName: string) {
    if (newName) {
      this.communityName = newName;
    }
    this.closeEditNameModal();
  }

  public openIsSelectingLevelModal() {
    this.isSelectingLevelModalOpen = true;;
  }

  public closeIsSelectingLevelModal() {
    this.isSelectingLevelModalOpen = false;;
  }

  public selectLevelModal() {
    this.openIsSelectingLevelModal();
    this.closeEditNameModal();
  }

  public getName() {
    return this.translate.instant('COMMUNITY.CURRENT_NAME') + ' ' + this.communityName;
  }

  public formatearFecha(fechaOld: string): string {
    if (fechaOld) {
      const locale = this.translate.currentLang;
      const fecha = new Date(fechaOld);
      return fecha.toLocaleDateString(locale, {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } else {
      return "--"
    }
  }

  public saveTheCommunity() {
    this.baselineData.baseline.name = this.communityName;
    this.baselineData.baseline.description = this.position ?? "-";
    if (this.keycloak.isLoggedIn()) {
      this.goNext();
    } else {
      this.keycloak.login();
      this.sessionStorage.setObject("baseline", {
        baselineData: this.baselineData,
        coords: this.coords,
        selectedCardWelcome: 0,
        steps: 4
      })
    }
  }

  private initMap(): void {
    this.map = L.map('map-community', {
      center: [this.coords[1], this.coords[0]],
      zoom: 15,
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

    if (!this.isAdvanced) {
      if (this.baselineData) {
        this.baselineData?.baseline?.building_asset_context.forEach((context: any) => {
          const geom = this.extractCoordinates(context?.building?.geom);
          if (geom) {
            this.marker = L.marker(geom, { icon: this.icon }).addTo(this.map);
            this.marker.on('click', () => this.onMarkerClick(geom));
          }
        });
      }
    } else {
      this.drawPolygons(this.baselineData?.baseline?.building_asset_context);
    }
  }

  private onMarkerClick(geom: any) {
    this.map.flyTo(geom, 18);
  }

  private extractCoordinates(geom: string): [number, number] | null {
    const match = geom.match(/POINT\(([-\d.]+) ([-\d.]+)\)/);
    return match ? [parseFloat(match[2]), parseFloat(match[1])] : null;
  }

  private drawPolygons(buildings: any) {
    this.polygons = [];

    buildings.map((build: any) => {
      this.polygons.push({
        coordinates: this.WKTService.WktToCoordsPolygon("POLYGON", build?.building?.geom)
      })
    });

    this.polygons.forEach(polygon => {

      this.polygonsLayer = L.polygon(polygon.coordinates, {
        weight: 3,
        color: "#3B62AB",
        fillColor: '#3B62AB',
        fillOpacity: 0.5
      }).addTo(this.map);

    });
  }

//#region KPIs

scrollRight() {
  this.scrollContainer.nativeElement.scrollBy({
    left: 150,
    behavior: 'smooth' 
  });
}

scrollLeft() {
  this.scrollContainer.nativeElement.scrollBy({
    left: -150, 
    behavior: 'smooth'
  });
}

//#endregion

}