import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { CardInfo, ChildsNavigation, NavigationControl, StepChildNavigation, achievementCard, achivementCardArray, cardArrayModule, secNavigationMenu } from '../../../data/types';
import { TranslateService } from '@ngx-translate/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FindCommunityService } from '../../../services/find-community.service';
import { AlertsService } from '../../alerts/alerts.service';
import L from 'leaflet';
import { WKTService } from '../../../services/WKT.service';
import { KeycloakService } from 'keycloak-angular';
import { SessionStorageService } from '../../../services/session-storage.service';
import { KeycloakToolsService } from '../../../services/keycloak-tools.service';
import { APP_ROUTES } from '../../../data/routes';
import { ViewportScroller } from '@angular/common';
import { BasicBaselineService } from '../../../services/basic-baseline.service';

@Component({
  selector: 'app-our-community',
  templateUrl: './our-community.component.html',
  styleUrls: ['./our-community.component.scss']
})
export class OurCommunityComponent implements OnInit {

  @Input() communityName: string = "";
  @Input() editMode: boolean = true;
  @Input() isSelectingLevelModalOpen: boolean = false;
  @Input() isEditNameModalOpen: boolean = false;
  @Input() isConfigModalOpen: boolean = false;
  @Input() isDeleteModalOpen: boolean = false;
  @Input() id: number = -1;
  @Input() showHint: boolean = false;
  @Input() buildingIconName: string = "Multi family house.svg";
  @Input() coords: any = [43.3639000, -2.5354000];
  @Input() mapLoading: boolean = false;
  @Input() loading: boolean = false;
  @Input() loadingAlternatives: boolean = false;
  @Input() isUserLogged: boolean = false;
  @Input() communityList: any;
  @Input() childs: any;
  @Input() cardArray: CardInfo[] = [];
  @Input() openCompare: boolean = false;
  @Input() alternatives: any = [];
  @Input() kpis: any;
  @Input() kpisData: any = [];
  @Input() isAlternative: boolean = false;
  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();

  // public achivementCardArray: achievementCard[] = achivementCardArray;

  @ViewChild('scrollContainer', { static: true }) scrollContainer!: ElementRef;

  public fechaCreacion?: string;
  public localizacion?: string;
  public loadingName: boolean = false;

  public secNavigationMenu = secNavigationMenu;

  private communityID: number = -1;
  public community: any;
  public tempName?: string;

  public marker: any;
  public polygons: any[] = [];
  public polygonsLayer: any;
  public loadingAll: boolean = false;

  public currentPage = 'MENU.DESKTOP.MY_COMMUNITY.SUMMARY';

  private icon: any = L.icon({
    iconUrl: './assets/icons/map-postion.svg',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
  });

  private map: any = null;

  public kpisCompare: any;
  public isLoadingCompare: boolean = true;

  constructor(
    private translate: TranslateService,
    private activatedRoute: ActivatedRoute,
    private findComunityService: FindCommunityService,
    private alertsService: AlertsService,
    private WKTService: WKTService,
    private readonly keycloak: KeycloakService,
    private sessionStorage: SessionStorageService,
    private findCommunityService: FindCommunityService,
    private keyToolsService: KeycloakToolsService,
    private router: Router,
    private viewportScroller: ViewportScroller,
    private basicBaselineService: BasicBaselineService,
    private Aroute: ActivatedRoute
  ) { }

  public random1: number = 500;
  public random2: number = 500;

  ngOnInit() {
    this.isUserLogged = this.keycloak.isLoggedIn();
    if (this.id > 0) {
      this.onIdChange();
      this.communityID = this.id;
      this.getCommunityById();
    } else {
      if (!this.isUserLogged) {
        this.keycloak.login();
      } else {
        this.Aroute.url.subscribe(segments => {
          const urlString = segments.map(segment => segment.path).join('/');

          if (urlString.includes(APP_ROUTES.ALTERNATIVE)) {
            this.isAlternative = true;
          }
        });
        this.activatedRoute.params.subscribe(params => {

          this.loadingAll = false;
          this.onIdChange();
          const paramId = params['id'];
          this.communityID = Number(paramId);
          if (this.communityID > 0) {
            this.getCommunityById();
            this.getCommunityList();
          } else {
            this.loadingAll = true;
            this.getCommunityList();
          }
        });
      }
    }
  }

  public back() {
    this.goBack.emit();
  }

  private onIdChange(): void {
    if (this.map) {
      this.map.remove();
      this.map = undefined;
    }

    this.initMap();
    this.random1 = this.getRandomNumer();
    this.random2 = this.getRandomNumer();

  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    this.next.emit();
  }

  public logIn() {
    if (!this.isUserLogged) {
      this.sessionStorage.setObject("baseline", {
        selectedCardWelcome: 1,
        steps: 1,
        id: this.id
      })
      this.keycloak.login();
    }
  }

  //#region Modal open/close

  public openConfigModal() {
    if (this.id || this.communityID > 0) {
      this.isConfigModalOpen = true;
      this.closeEditNameModal();
      this.closeDeleteModal();
    }
  }

  public closeConfigModal() {
    this.isConfigModalOpen = false;
  }

  public openEditNameModal() {
    this.closeConfigModal();
    this.isEditNameModalOpen = true;
  }

  public closeEditNameModal() {
    this.isEditNameModalOpen = false;
  }


  public openDeleteModal() {
    this.closeConfigModal();
    this.isDeleteModalOpen = true;
  }

  public closeDeleteModal() {
    this.isDeleteModalOpen = false;
  }

  public openIsSelectingLevelModal() {
    this.closeConfigModal();
    this.isSelectingLevelModalOpen = true;;
  }

  public closeIsSelectingLevelModal() {
    this.isSelectingLevelModalOpen = false;;
  }

  //#endregion

  public saveNewNameCommunity() {
    if (this.tempName) {
      this.loadingName = true;
      this.basicBaselineService.changeCommunityName(this.communityID, this.tempName).subscribe({
        next: (community: any) => {
          this.communityName = this.tempName ?? "";
          this.closeEditNameModal();
          this.loadingName = false;
        },
        error: (err: any) => {
          console.error(err)
          this.loadingName = false;
          this.alertsService.error(`An error occurred while deleting the community. Error type ${err.statusText}: ${err.error.detail}`)
        }
      })
    }
  }

  public selectLevelModal() {
    this.openIsSelectingLevelModal();
    this.closeEditNameModal();
  }

  public deleteCommunity() {
    this.closeDeleteModal();
    this.loading = true;
    if (this.communityID !== -1) {
      this.findComunityService.deleteCommunity(this.communityID).subscribe({
        next: (community: any) => {
          this.loading = false;
          this.communityList = this.communityList.filter((community: any) => community.id !== this.communityID)
          if (this.communityList && this.communityList.length > 0) {
            this.communityID = this.communityList[0].id;
            const route = APP_ROUTES.COMMUNITY + "/" + this.communityID;
            this.router.navigate(["/" + route])
          } else {
            this.router.navigate(["/" + APP_ROUTES.FORMULARY])
          }
          console.info("delete community: " + community.id)
        },
        error: (err: any) => {
          this.loading = false;
          console.error(err)
          this.alertsService.error(`An error occurred while deleting the community. Error type ${err.statusText}: ${err.error.detail}`)
        }
      })
    } else {
      this.alertsService.error(`An error occurred while deleting the community.`)
      this.loading = false;
    }
  }

  public getCommunityById() {
    this.mapLoading = true;
    this.loading = true;
    this.findComunityService.getCommunityByIdComplete(this.communityID).subscribe({
      next: (community: any) => {
        this.community = community.context;
        this.kpis = community.kpis
        this.kpisCompare = {
          context: this.kpis
        }
        this.generateKpiArray();
        if (community?.context?.context_parent) {
          this.isAlternative = true
        }
        this.localizacion = community.context?.description;
        this.fechaCreacion = community.context?.creation_date;
        this.communityName = community.context?.name;
        this.loading = false;
        this.getCommunityAltenative(community.context.id);
        this.generatePoints();
      },
      error: (err: any) => {
        this.loading = false;
        console.error(err)
        this.alertsService.error(`An error occurred while getting the community. Error type ${err.statusText}: ${err.error.detail}`)
      }
    })
  }

  private getCommunityAltenative(communityId: number) {
    if (communityId && !this.isAlternative) {
      this.findComunityService.getCommunityAlternatives(communityId).subscribe({
        next: (alternatives: any) => {
          this.loadingAlternatives = false;
          this.alternatives = alternatives;
          this.createCardsAlternative();
        },
        error: (err: any) => {
          this.loadingAlternatives = false;
          console.error(err)
          this.alertsService.error(`An error occurred. Error type ${err.statusText}: ${err.error.detail}`)
        }
      })
    }
  }

  private createCardsAlternative() {
    if (this.alternatives) {
      this.cardArray = [];
      this.alternatives.forEach((alter: any) => {
        this.cardArray.push({
          title: alter.name,
          description: alter.description,
          id: alter.id,
          show: true,
          infoIcon: false,
          iconName: 'layers-blue.svg'
        } as CardInfo)

      });
    }

  }

  public navigateToAlternative(alternative: any) {
    const route = APP_ROUTES.COMMUNITY + "/" + this.communityID + "/" + APP_ROUTES.ALTERNATIVE + "/" + this.alternatives[alternative].id;
    this.router.navigate([route])
  }

  //#region  map

  private initMap(): void {
    this.map = L.map('map-our-community', {
      center: [this.coords[0], this.coords[1]],
      zoom: 4,
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


  private generatePoints() {

    if (this.community) {
      if (this.community?.building_asset_context[0]?.building?.geom.includes('POINT')) {
        this.map.setView(this.extractCoordinates(this.community?.building_asset_context[0]?.building?.geom), 15);
        this.community?.building_asset_context.forEach((context: any) => {
          const geom = this.extractCoordinates(context?.building?.geom);
          if (geom) {
            this.marker = L.marker(geom, { icon: this.icon }).addTo(this.map);
            this.marker.on('click', () => this.onMarkerClick(geom));
          }
        });
      } else {
        this.drawPolygons(this.community?.building_asset_context);
      }
    }
    this.mapLoading = false;
  }

  private onMarkerClick(geom: any) {
    this.map.flyTo(geom, 18);
  }

  private extractCoordinates(geom: string): [number, number] | null {
    let match = geom.match(/POINT\(([-\d.]+) ([-\d.]+)\)/);
    if (!match)
      match = geom.match(/POINT \(([-\d.]+) ([-\d.]+)\)/);
    return match ? [parseFloat(match[2]), parseFloat(match[1])] : null;
  }

  private drawPolygons(buildings: any) {
    this.polygons = [];
    let isMultiPol: boolean = false;

    buildings.map((build: any) => {
      if (build?.building?.geom?.includes('MULTIPOLYGON')) {
        isMultiPol = true;
        this.polygons.push({
          coordinates: this.WKTService.WktToCoordsMultiPolygon(build?.building?.geom)
        })
      } else {
        this.polygons.push({
          coordinates: this.WKTService.WktToCoordsPolygon("POLYGON", build?.building?.geom) ? this.WKTService.WktToCoordsPolygon("POLYGON", build?.building?.geom) : this.WKTService.WktToCoordsPolygon("POLYGON ", build?.building?.geom)
        })
      }
    });

    if (isMultiPol)
      this.map.setView(this.polygons[0].coordinates[0][0], 15)
    else
      this.map.setView(this.polygons[0].coordinates[1], 15);

    this.polygons.forEach(polygon => {
      this.polygonsLayer = L.polygon(polygon.coordinates, {
        weight: 3,
        color: "#3B62AB",
        fillColor: '#3B62AB',
        fillOpacity: 0.5
      }).addTo(this.map);

    });
    this.mapLoading = false;
  }

  //#endregion

  //#region CommunityList

  private getCommunityList() {
    this.keyToolsService.getUserUID().then(uid => {
      this.findCommunityService.getCommunityList().subscribe({
        next: (data: any) => {
          this.communityList = data.filter((da: any) => da.author === uid && da.context_parent === null);
          const alternativeList = data.filter((da: any) => da.author === uid && da.context_parent !== null) ?? [];
          alternativeList.forEach((alter: any) => {
            const index = this.communityList.findIndex((comu: any) => comu.id === alter.context_parent);
            if (index != -1) {
              let community = this.communityList[index];
              community.alternatives = community.alternatives ? community.alternatives : [];
              community.alternatives.push(alter);
              this.communityList[index] = community;
            }
          });

          this.updateCommunityList();
          if (this.communityID < 0 && this.communityList) {
            if (this.communityList.length > 0) {
              this.communityID = this.communityList[0].id;
              const route = APP_ROUTES.COMMUNITY + "/" + this.communityID;
              this.router.navigate(["/" + route])
            } else {
              this.viewportScroller.scrollToPosition([0, 0]);
              this.router.navigate(["/" + APP_ROUTES.FORMULARY], { queryParams: { explore_my_community: 'true' } });
            }
          }
        }, error: (err: any) => {
          console.error(err.message)
        }
      })
    })
  }

  private updateCommunityList() {
    if (this.communityList) {
      this.childs = [];
      this.communityList.forEach((community: any) => {
        this.childs.push({
          active: false,
          name: community.name,
          url: "/community/" + community.id,
          id: community.id,
          alternative: {
            name: "MENU.DESKTOP.MY_COMMUNITY.ALTERNATIVES",
            icon: "layers-blue.svg",
            url: APP_ROUTES.COMMUNITY + "/" + community.id + "/" + APP_ROUTES.ALTERNATIVES,
            childs: community.alternatives ? community.alternatives.map((alter: any) => this.transformToChildsNavigation(alter)) : null
          } as NavigationControl,
        } as ChildsNavigation)
      });
    }
    (this.secNavigationMenu[0] as any).childs = this.childs;
    this.changeActiveCommunity(-1);
  }

  private transformToChildsNavigation(community: any) {
    return {
      active: false,
      name: community.name,
      url: APP_ROUTES.COMMUNITY + "/" + community.context_parent + "/" + APP_ROUTES.ALTERNATIVE + "/" + community.id,
      id: community.id,
    } as ChildsNavigation
  }

  public changeActiveCommunity(community: any) {
    const alternativeID = community.alternative;
    community = community.parent;

    (this.secNavigationMenu[0].childs ?? []).forEach((nav: any, index) => {
      nav.active = false;
      (this.secNavigationMenu[0] as any).childs[index].active = false;
      if (index === community && !alternativeID) {
        (this.secNavigationMenu[0] as any).childs[index].active = true;
        const comm = (this.secNavigationMenu[0] as any).childs[index];
        (this.secNavigationMenu[0] as any).childs[index] = comm;
      }

      if (index === community && alternativeID) {
        nav?.alternative?.childs.forEach((alter: any, indexAlter: number) => {
          if (alter.id === alternativeID) {
            (this.secNavigationMenu[0] as any).childs[index].active = true;
            (this.secNavigationMenu[0] as any).childs[index].alternative.childs[indexAlter].active = true;
          }
        });
      }

    });
    if (this.communityID > 0) {
      (this.secNavigationMenu[0] as any).childs.find((comm: any) => comm.id === this.communityID).active = true;
    }
  }

  //#endregion

  //#region Navigate

  goToRefineCommunity() {
    this.router.navigate([`/${APP_ROUTES.COMMUNITY}/${this.communityID}/${APP_ROUTES.REFINE}`]);
  }

  goToAlternativeList() {
    this.router.navigate([`/${APP_ROUTES.ALTERNATIVES}/${this.communityID}`]);
  }

  public goToNewAlternative() {
    this.router.navigate(["/" + APP_ROUTES.FORMULARY, this.communityID], { queryParams: { create_alternatives: 'true' } });
  }


  //#endregion

  //#region KPI

  private generateKpiArray() {
    if (this.kpis) {
      let kpisD = [];
      kpisD.push(
        {
          value: this.convertEnergy(this.sum(this.kpis['total_primary_energy_[kWh]'].value)).value,
          unit: this.convertEnergy(this.sum(this.kpis['total_primary_energy_[kWh]'].value)).unit,
          kpi: this.kpis['total_primary_energy_[kWh]'].value,
          card: this.translate.instant('KPI.PRIMARY_ENERGY_CONSUMPTION.CARD')
            .replace("{total_primary_energy_intensity}", this.kpis['total_primary_energy_intensity'].value.toFixed(2))
            .replace("{XXX higher/lower/equal}", this.compareValues(this.kpis['total_primary_energy_intensity'].value, this.kpis['national_average_total_primary_energy_intensity'].value))
            .replace("{national_average_total_primary_energy_intensity}", this.kpis['national_average_total_primary_energy_intensity'].value.toFixed(2)),
          messages: [this.sum(this.kpis['EquivalentTVHours_[h]'].value), this.sum(this.kpis['PizzaConsumptionComparison_[pizza]'].value), this.sum(this.kpis['ElectricCarChargingEstimation_[charges]'].value)]
        }
      );

      kpisD.push(
        {
          value: this.convertMoney(this.sum(this.kpis['households_costs_[€]'].value)).value,
          unit: this.convertMoney(this.sum(this.kpis['households_costs_[€]'].value)).unit,
          kpi: this.kpis['households_costs_[€]'].value,
          card: this.translate.instant('KPI.ENERGY_COST.CARD')
            .replace("{total_energy_cost_intensity}", this.kpis['total_energy_cost_intensity'].value.toFixed(2))
            .replace("{XXX higher/lower/equal}", this.compareValues(this.kpis['total_energy_cost_intensity'].value, this.kpis['national_average_total_energy_cost_intensity'].value))
            .replace("{national_average_total_energy_cost_intensity}", this.kpis['national_average_total_energy_cost_intensity'].value.toFixed(2))
        }
      );

      kpisD.push(
        {
          value: this.convertWeight(this.sum(this.kpis.Total_co2.value)).value,
          unit: this.convertWeight(this.sum(this.kpis.Total_co2.value)).unit,
          kpi: this.kpis.Total_co2.value,
          card: this.translate.instant('KPI.GHG_EMISSIONS.CARD')
            .replace("{total_CO2_intensity}", this.kpis['total_CO2_intensity'].value.toFixed(2))
            .replace("{XXX higher/lower/equal}", this.compareValues(this.kpis['total_CO2_intensity'].value, this.kpis['national_average_total_CO2_intensity'].value))
            .replace("{national_average_total_CO2_intensity}", this.kpis['national_average_total_CO2_intensity'].value.toFixed(2)),
          messages: [this.sum(this.kpis['CarbonEmissionsPerKilometer_[km]'].value), this.sum(this.kpis['streamingEmissionsImpact_[hours]'].value)],

        }
      );

      kpisD.push(
        {
          value: this.convertMoney(this.kpis.total_capex.value).value,
          unit: this.convertMoney(this.kpis.total_capex.value).unit,
          kpi: this.kpis.total_capex,
          card: this.translate.instant('KPI.INVESTMENT.CARD')
            .replace("{total_capex}", this.kpis['total_capex'].value.toFixed(2))
            .replace("{total_lifetime_costs}", this.kpis['total_lifetime_costs'].value.toFixed(2))
            .replace("{payback_period_years}", this.kpis['payback_period_years'].value.toFixed(2))
            .replace("{total_savings}", this.kpis['total_savings'].value.toFixed(2))
        }
      );

      this.kpisData = kpisD;
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

  private convertWeight(value: number, decimals: number = 2) {
    if (value >= 1_000_000) {
      return {
        value: (value / 1_000_000).toFixed(decimals),
        unit: 't'
      };
    } else if (value >= 1000) {
      return {
        value: (value / 1000).toFixed(decimals),
        unit: 'Kg'
      };
    } else {
      return {
        value: value.toFixed(decimals),
        unit: 'g'
      };
    }
  }

  private convertMoney(value: number, decimals: number = 2) {
    if (value >= 1_000_000) {
      return {
        value: (value / 1_000_000).toFixed(decimals),
        unit: 'M€'
      };
    } else if (value >= 1000) {
      return {
        value: (value / 1000).toFixed(decimals),
        unit: 'k€'
      };
    } else {
      return {
        value: value.toFixed(decimals),
        unit: '€'
      };
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

  getRandomNumer() {
    return Math.floor(Math.random() * (1000 - 500 + 1)) + 500;
  }

  openKPInformation(index: number) {
    console.log(index)
  }

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

  //#region Alternative compare info

  public loadAlternativeKpis(id: number) {
    this.getAlternativeById(id);
  }

  public getAlternativeById(id: number) {
    this.isLoadingCompare = true;
    this.findComunityService.getCommunityByIdComplete(id).subscribe({
      next: (alternative: any) => {
        this.kpisCompare[alternative?.context?.name] = alternative?.kpis;
        setTimeout(() => {
          this.isLoadingCompare = false;
        }, 10);
      },
      error: (err: any) => {
        console.error(err)
        this.isLoadingCompare = false;
        this.alertsService.error(`An error occurred while getting the alternative. Error type ${err.statusText}: ${err.error.detail}`)
      }
    })
  }

  //#endregion

}
/**Achivements no developed */
// public mouseEnter(index: number, type: number) {
//   if (type === 0 && !this.achivementCardArray[index].complete && !this.achivementCardArray[index].disabled) {
//     this.achivementCardArray[index].iconName = this.achivementCardArray[index].iconName.replace('.svg', '-hover.svg')
//   }
// }

// public mouseLeave(index: number, type: number) {
//   if (type === 0 && !this.achivementCardArray[index].complete && !this.achivementCardArray[index].disabled) {
//     this.achivementCardArray[index].iconName = this.achivementCardArray[index].iconName.replace('-hover', '')
//   }
// }