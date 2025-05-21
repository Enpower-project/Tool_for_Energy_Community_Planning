import { Component, OnInit } from '@angular/core';
import { APP_ROUTES } from '../../../data/routes';
import { CanComponentDeactivate } from '../../../services/can-deactivate.guard';
import { Location, ViewportScroller } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { BasicBaselineService } from '../../../services/basic-baseline.service';
import { NavigationService } from '../../../services/navigation.service';
import { MapService } from '../../../services/map.service';
import { SessionStorageService } from '../../../services/session-storage.service';
import { AlertsService } from '../../alerts/alerts.service';
import { IntermediateBaselineService } from '../../../services/intermediate-baseline.service';
import { WKTService } from '../../../services/WKT.service';
import { NavigationControl, priNavigationMenu, secNavigationMenu } from '../../../data/types';
import { KeycloakService } from 'keycloak-angular';
import { KeycloakToolsService } from '../../../services/keycloak-tools.service';
import { FindCommunityService } from '../../../services/find-community.service';
import { AlternativesService } from '../../../services/alternatives.service';

@Component({
  selector: 'app-steps',
  templateUrl: './steps.component.html',
  styleUrls: ['./steps.component.scss']
})
export class StepsComponent implements OnInit, CanComponentDeactivate {

  constructor(
    private router: Router,
    private location: Location,
    private basicBaselineService: BasicBaselineService,
    private navigationService: NavigationService,
    private viewportScroller: ViewportScroller,
    private mapService: MapService,
    private sessionStorage: SessionStorageService,
    private alertsService: AlertsService,
    private intermediateBaselineService: IntermediateBaselineService,
    private wktService: WKTService,
    private readonly keycloak: KeycloakService,
    private keyToolsService: KeycloakToolsService,
    private findCommunityService: FindCommunityService,
    private alternativesService: AlternativesService,
    private activatedRoute: ActivatedRoute
  ) { }

  public showLoading: boolean = false;

  public navigateRoute?: string;
  public openModal: boolean = false;
  public steps: number = 0;
  public STEP_TYPE = STEP_TYPE;
  public stepHistory: any = [];
  public nextUrl: any;
  public APP_ROUTES = APP_ROUTES;
  public currentPage = "MENU.DESKTOP.MENU.GET_STARTED.HEADING"

  public buildingUseList: any;
  public commonProfileList: any;

  public isAdvanced: boolean = false;

  public communityCoords: any;

  private navegateToTheCreatedComunnity: boolean = false;

  /*Find your community */
  public loadingFind: boolean = false;

  /*Community demo*/
  public loadingDemo: boolean = false;

  /*Our community*/
  public communityId: number = -1;

  /*Adress selector */
  public maker: any;

  /*Card selector*/
  public cardObject: any;
  public alternativeList: any;
  public countryAlterntive?: string;
  public loadingCardSelector: boolean = false;

  /*Welcome component*/
  public selectedCardWelcome: number = -1;

  /*Building selector*/
  public buildingsInfo: any;
  public baselineData: any
  public positionCommunityDemo: any;

  /*recommend actions*/
  public recommendedActions: any;

  public numBuildings: number = 2;

  public openModalCreateCommunity: boolean = false;

  public priNavigationMenu: NavigationControl[] = priNavigationMenu;
  public secNavigationMenu: NavigationControl[] = secNavigationMenu;
  public communityList: any;
  public clickShowCommunity: boolean = false;
  public openCreateCommunity: boolean = false;
  private uid!: string;

  public reloadSignal: boolean = false;

  ngOnInit() {

    this.reloadAlternativeOption();

    const routerLink = this.router.url;
    this.getCatalogs()
    if (routerLink.includes('explore_my_community')) {
      this.goToExploreCommunity();
    }

    if (routerLink.includes('guided_modeling')) {
      this.goToCreateCommunity();
    }

    if (routerLink.includes('create_alternatives')) {
      this.goToCreateAlternatives();
    }

    const baselineObject: any = this.sessionStorage.getObject("baseline");
    if (baselineObject) {
      this.registerWelcomeStep();
      if (baselineObject?.id) {
        this.communityId = baselineObject?.id;
        this.getCommunityInfoAndNavigate();
      } else {
        this.baselineData = baselineObject?.baselineData;
        this.communityCoords = baselineObject?.coords;
      }
      this.selectedCardWelcome = baselineObject?.selectedCardWelcome;
      this.steps = baselineObject?.steps;
      this.sessionStorage.removeObject("baseline");
    }
    this.setCurrentPage();
  }

  public goToCreateCommunity() {
    this.closeModalAlternatives();
    if (this.selectedCardWelcome !== this.STEP_TYPE.CREATE_COMMUNITY) {
      this.registerWelcomeStep();
      this.location.replaceState(APP_ROUTES.FORMULARY);
      this.steps = 1;
      this.selectedCardWelcome = this.STEP_TYPE.CREATE_COMMUNITY;
    }
  }

  public goToCreateAlternatives() {
    this.activatedRoute.params.subscribe(params => {
      const paramId = params['id'];
      const communityId = Number(paramId);

      this.closeModalAlternatives();
      if (this.selectedCardWelcome !== this.STEP_TYPE.CREATE_ALTERNATIVES) {
        this.registerWelcomeStep();
        this.location.replaceState(APP_ROUTES.FORMULARY);
        if (communityId) {
          this.steps = 1;
          this.loadingFind = true;
          this.findCommunityService.getCommunityById(communityId).subscribe({
            next: (data: any) => {

              this.getCountry(data);
            }, error: (err: any) => {
              console.error(err.message)
            }
          })
        } else {
          this.steps = 1;
        }
        this.selectedCardWelcome = this.STEP_TYPE.CREATE_ALTERNATIVES;
      }
    });

  }

  public goToExploreCommunity() {
    this.closeModalAlternatives();
    if (this.selectedCardWelcome !== this.STEP_TYPE.CREATE_ALTERNATIVES) {
      this.registerWelcomeStep();
      this.location.replaceState(APP_ROUTES.FORMULARY);
      this.steps = 1;
      this.selectedCardWelcome = this.STEP_TYPE.CREATE_ALTERNATIVES;
    }
  }

  canDeactivate(): boolean {
    if (this.openModal === true || this.selectedCardWelcome === STEP_TYPE.EXPLORE_COMMUNITY || this.selectedCardWelcome >= 3 || this.steps === 0 || this.navegateToTheCreatedComunnity === true) {
      return true;
    } else {
      this.openModal = true;
    }
    return false;
  }

  public returnHome() {
    this.router.navigate(['/' + APP_ROUTES.HOME])
  }

  public goto(route: string) {
    this.router.navigate([route])
  }

  public closeIt() {
    this.nextUrl = this.navigationService.getNextUrl();
    if (this.nextUrl) {
      this.router.navigate([this.nextUrl])
      this.nextUrl = null;
    } else {
      this.router.navigate(['/' + APP_ROUTES.HOME])
    }
  }

  public goBack() {
    if (this.stepHistory.length > 0) {
      const newStep = this.stepHistory[this.stepHistory.length - 1];
      this.steps = newStep.step;
      this.selectedCardWelcome = newStep.type;
      this.setCurrentPage();
      this.stepHistory.pop();
    } else {
      this.returnHome();
    }
  }

  public registerStep() {
    this.stepHistory.push({
      step: this.steps,
      type: this.selectedCardWelcome
    })
  }

  public registerWelcomeStep() {
    this.steps = 0;
    this.registerStep();
  }

  public next() {
    this.registerStep();
    this.viewportScroller.scrollToPosition([0, 0]);
    this.steps = this.steps !== 5 ? this.steps + 1 : 5;
    this.setCurrentPage();
  }

  public setNumerBuildings(buildings: number) {
    if (buildings > 50) {
      buildings = 50;
    }
    this.numBuildings = buildings;
    this.next();
  }

  private getCatalogs() {
    this.basicBaselineService.getBuildingUsesList().subscribe({
      next: (data: any) => {
        this.buildingUseList = data;
      }, error: (err: any) => {
        console.error(err.message);
      }
    });

    this.basicBaselineService.getCommonProfileList().subscribe({
      next: (data: any) => {
        this.commonProfileList = data;
      }, error: (err: any) => {
        console.error(err.message);
      }
    });
  }

  changeFormStep(newStep: any) {
    if (newStep.selectedCardWelcome === 2 && this.clickShowCommunity === true) {
      this.openModalCreateCommunity = true;
    } else {
      this.changeFormStepLogic(newStep);
    }
  }

  changeFormStepLogic(newStep: any) {
    this.registerStep();
    this.selectedCardWelcome = newStep.selectedCardWelcome;
    this.steps = newStep.steps;
  }

  changeCurrentPage(selected: number) {
    this.openModalCreateCommunity = false;
    this.selectedCardWelcome = selected;

    this.next();
  }

  private setCurrentPage() {
    if (this.steps === 0) {
      this.currentPage = "MENU.DESKTOP.MENU.GET_STARTED.HEADING"
    } else {
      switch (this.selectedCardWelcome) {
        case STEP_TYPE.CREATE_COMMUNITY:
          this.currentPage = "MENU.DESKTOP.MENU.GET_STARTED.CREATE_A_COMMUNITY.HEADING";
          break;
        case STEP_TYPE.EXPLORE_COMMUNITY:
          this.currentPage = "MENU.DESKTOP.MENU.GET_STARTED.EXPLORE_MY_COMMUNITY.HEADING";
          break;
        case STEP_TYPE.CREATE_ALTERNATIVES:
          this.currentPage = "MENU.DESKTOP.MENU.GET_STARTED.CREATE_ALTERNATIVES.HEADING";
          break;
        default:
          this.currentPage = "MENU.DESKTOP.MENU.GET_STARTED.LEARN_AND_RESEARCH";
          break;
      }
    }
  }

  public closeModal() {
    this.currentPage = "";
    this.openModal = false;
    setTimeout(() => {
      this.setCurrentPage();
    });
  }

  public navigateModalDeactivate() {

    if (this.navigateRoute) {
      this.router.navigate(['/' + this.navigateRoute])
      this.clearNavigateRoute();
    } else {
      this.returnHome();
    }
  }

  public clearNavigateRoute() {
    this.navigateRoute = undefined;
  }

  //#region Card-selector

  public getCountryAlternative(community: any) {
    this.countryAlterntive = community.country;
    this.next();
  }

  public setCardSelection(card: any) {
    this.loadingCardSelector = true;
    this.cardObject = card;
    const alternativeObject = {
      "goals": `${card.card.id}`,
      "country": this.countryAlterntive
    }
    this.alternativesService.postAlternativeConfig(alternativeObject).subscribe({
      next: (list: any) => {
        this.alternativeList = list;
        this.next();
        this.loadingCardSelector = false;
      },
      error: (err: any) => {
        console.error(err)
        this.alertsService.error(`An error occurred while getting the alternatives list. Error type ${err.statusText}: ${err.error.detail}`)
      }
    })
  }

  //#endregion

  //#region building-selector

  public setBuildingConf(inf: any) {
    this.showLoading = true;
    this.buildingsInfo = inf;
    if (!this.buildingsInfo.advanced) {
      this.isAdvanced = false;
      this.postBasicBaselineData();
    } else {
      this.isAdvanced = true;
      this.postIntermidateBaselineData();
    }
  }

  public postBasicBaselineData() {

    const lat = this.maker.getLatLng().lat;
    const lng = this.maker.getLatLng().lng;
    const data = {
      location: this.wktService.CoordsToWKT("Point", [lng, lat]),
      num_building: this.numBuildings,
      building_use_id: this.buildingsInfo.type,
      common_profile: this.buildingsInfo.profile
    }

    this.basicBaselineService.postData(data).subscribe({
      next: (data: any) => {
        this.baselineData = data;
        this.communityCoords = this.wktService.WktToCoords("POINT", data?.baseline?.building_asset_context[0]?.building?.geom)

        this.mapService.getLocationInfo(this.communityCoords[1], this.communityCoords[0]).subscribe({
          next: (position: any) => {
            this.next();
            this.positionCommunityDemo = position?.address.province;
            this.showLoading = false;
          },
          error: (err: any) => {
            console.error(err)
            this.alertsService.error(`An error occurred while getting the location info. Error type ${err.statusText}: ${err.error.detail}`)
            this.showLoading = false;
          }
        })
      }, error: (err: any) => {
        console.error(err)
        this.alertsService.error(`An error occurred while creating the community. Error type ${err.statusText}: ${err.error.detail}`)
        this.showLoading = false;
      }
    });
  }

  public postIntermidateBaselineData() {

    const lat = this.maker.getLatLng().lat;
    const lng = this.maker.getLatLng().lng;
    const data = this.buildingsInfo.buildings.map((building: any) => {
      return {
        geom: this.wktService.CoordsToWKT(building.buildingId.geometry.type, building.buildingId.geometry.coordinates),
        construction_year: this.intermediateBaselineService.transformIdToYear(building.buildingYear),
        subdivision_community: building.dwellings,
        subdivision_total: building.members,
        occupants: building.occupants,
        building_use_id: building.buildingType,
        common_profile_id: building.comunnityProfile,
      }
    }
    )

    this.intermediateBaselineService.postData(data).subscribe({
      next: (data: any) => {
        this.baselineData = data;
        this.communityCoords = [lng, lat]
        this.mapService.getLocationInfo(lat, lng).subscribe({
          next: (position: any) => {
            this.next();
            this.positionCommunityDemo = position?.address.province;
            this.showLoading = false;
          },
          error: (err: any) => {
            console.error(err)
            this.alertsService.error(`An error occurred while getting the location info. Error type ${err.statusText}: ${err.error.detail}`)
            this.showLoading = false;
          }
        })
      }, error: (err: any) => {
        console.error(err)
        this.alertsService.error(`An error occurred while creating the community. Error type ${err.statusText}: ${err.error.detail}`)
        this.showLoading = false;
      }
    });
  }

  //#endregion

  //#region access alternatives

  public createYourNewCommunity() {
    this.registerStep();
    this.selectedCardWelcome = this.STEP_TYPE.CREATE_COMMUNITY;;
    this.steps = 1;
  }

  //#endregion

  //#region community demo

  public generateCommunity() {
    this.registerStep();
    this.selectedCardWelcome = this.STEP_TYPE.CREATE_ALTERNATIVES;;
    this.steps = 1;
  }

  public saveCommunity(baselineData: any) {
    this.loadingDemo = true;
    baselineData.baseline.author = this.uid;
    this.basicBaselineService.postSaveCommunity(baselineData.baseline).subscribe({
      next: (data: any) => {
        this.navegateToTheCreatedComunnity = true;
        this.goToCommunityId(data.id);
        // this.getCountry(data);
      }, error: (err: any) => {
        console.error(err.message);
        this.loadingDemo = false;
        this.alertsService.error(err.error.detail);
      }
    });
  }

  private getCountry(communnity: any) {

    let coords: any = this.wktService.WktToCoords("POINT ", communnity.building_asset_context[0].building.geom);

    if (communnity.building_asset_context[0].building.geom.includes("MULTIPOLYGON")) {
      let coordsMulty = this.wktService.WktToCoordsMultiPolygon(communnity.building_asset_context[0].building.geom)[0];
      coords = coordsMulty[0].reverse();
    } else if (communnity.building_asset_context[0].building.geom.includes("POLYGON")) {
      coords = this.wktService.WktToCoordsPolygon("POLYGON ", communnity.building_asset_context[0].building.geom);
    }

    this.mapService.getLocationInfo(coords[1], coords[0]).subscribe({
      next: (data: any) => {
        this.countryAlterntive = data.address.country_code?.toUpperCase();
        this.selectedCardWelcome = STEP_TYPE.CREATE_ALTERNATIVES;
        this.steps = 2;
        this.setCurrentPage();
        this.reloadSignal = !this.reloadSignal;
        this.reloadAlternativeOption();
        this.loadingDemo = false;
        this.loadingFind = false;
      }, error: (err: any) => {
        console.error(err.message)
      }
    })
  }

  private reloadAlternativeOption() {
    if (!this.keycloak.isLoggedIn()) {
      (this.priNavigationMenu[1] as any).childs[2].disable = true;
      (this.priNavigationMenu[1] as any).childs[2].messageDisable = "ONBOARDING.ALERT.NO_LOG_IN";
    } else {
      (this.priNavigationMenu[1] as any).childs[2].disable = false;
      this.keyToolsService.getUserUID().then(uid => {
        this.uid = uid;
        this.findCommunityService.getCommunityList().subscribe({
          next: (data: any) => {
            this.communityList = data.filter((da: any) => da.author === uid && da.context_parent === null);
            this.clickShowCommunity = this.communityList?.length === 0;
          }, error: (err: any) => {
            console.error(err.message)
          }
        })
      });
    }
  }

  public closeModalAlternatives() {
    this.closeModal();
    this.openModalCreateCommunity = false;
  }

  //#endregion

  //#region Recommended-actions

  public setRecommendedActions(recommended: any) {
    this.recommendedActions = recommended;
    this.next();
  }

  //#endregion

  //#region scenario-component

  public createNewAlternative() {
    this.selectedCardWelcome = this.STEP_TYPE.CREATE_ALTERNATIVES;
    this.steps = 0;
    this.next();


  }

  //#endregion

  //#region Alternatives



  //#endregion

  //#region find-community

  private getCommunityInfoAndNavigate() {
    this.loadingFind = true;
    this.findCommunityService.getCommunityById(this.communityId).subscribe({
      next: (community: any) => {
        this.nextCommunity({
          card: {
            id: this.communityId
          },
          author: community.author
        })
      },
      error: (err: any) => {
        console.error(err)
        this.alertsService.error(`An error occurred while getting the community info. Error type ${err.statusText}: ${err.error.detail}`)
      }
    })
  }

  public goToCommunity(community: any) {
    const id = community.card.id;
    const route = APP_ROUTES.COMMUNITY + "/" + id;
    this.navigateRoute = route;
    this.goto("/" + route);
  }

  public goToCommunityId(id: number) {
    const route = APP_ROUTES.COMMUNITY + "/" + id;
    this.navigateRoute = route;
    this.goto("/" + route);
  }


  public nextCommunity(community: any) {

    this.keyToolsService.getUserUID().then(uid => {
      this.uid = uid;
      if (this.uid && this.uid === community?.author) {
        this.goToCommunity(community);
      } else {
        this.communityId = community.card.id;
        this.next();
      }
      this.loadingFind = false;
    })
  }

  //#endregion

}

enum STEP_TYPE {
  CREATE_COMMUNITY, EXPLORE_COMMUNITY, CREATE_ALTERNATIVES, LEARN, DEVELOP_MODEL, SIZE_COMMUNITY
};