import { ViewportScroller } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { KeycloakService } from 'keycloak-angular';
import { FindCommunityService } from '../../../services/find-community.service';
import { KeycloakToolsService } from '../../../services/keycloak-tools.service';
import { SessionStorageService } from '../../../services/session-storage.service';
import { AlertsService } from '../../alerts/alerts.service';
import { WKTService } from '../../../services/WKT.service';
import { BasicBaselineService } from '../../../services/basic-baseline.service';
import { APP_ROUTES } from '../../../data/routes';
import * as L from 'leaflet';
import { IntermediateBaselineService } from '../../../services/intermediate-baseline.service';

@Component({
  selector: 'app-refine-community',
  templateUrl: './refine-community.component.html',
  styleUrls: ['./refine-community.component.scss']
})
export class RefineCommunityComponent implements OnInit {

  private communityID: number = -1;
  public community: any;
  public loading: boolean = true;

  public buildingNumber: number = 0;
  public buildingUseList: any = [];
  public commonProfileList: any = [];
  public buildingsArray: any = [];
  public marker: any;
  public editmode: boolean = true;
  public buildingInfo: any;

  public loadingCreate: boolean = false;
  public coords: any;

  public loadingSaveCommunity: boolean = false;

  public newCommunityName: string = "";

  public description?: string;

  public baselineData: any;

  constructor(
    private activatedRoute: ActivatedRoute,
    private findComunityService: FindCommunityService,
    private alertsService: AlertsService,
    private basicBaselineService: BasicBaselineService,
    private router: Router,
    private intermediateBaselineService: IntermediateBaselineService,
    private wktService: WKTService,
    private readonly keycloak: KeycloakService,
    private readonly keyToolsService: KeycloakToolsService
  ) { }

  ngOnInit() {
    this.editmode = true;
    this.loading = true;
    this.getCatalogs();
    this.activatedRoute.params.subscribe(params => {
      const paramId = params['id'];
      this.communityID = Number(paramId);
      if (this.communityID > 0) {
        this.getCommunityById();
      } else {
      }
    });
  }

  public getCommunityById() {
    this.findComunityService.getCommunityById(this.communityID).subscribe({
      next: (community: any) => {
        this.community = community;
        this.validateUser();
        this.description = community?.description;
        this.buildingNumber = community?.building_asset_context?.length;
        this.generateFormArray(community?.building_asset_context);
        if (this.community?.building_asset_context[0]?.building?.geom.includes('POINT')) {
          const geom = this.extractCoordinates(this.community?.building_asset_context[0]?.building?.geom);
          if (geom) {
            this.marker = L.marker(geom);
          }
        }
        this.loading = false;
      },
      error: (err: any) => {
        console.error(err)
        this.alertsService.error(`An error occurred while getting the community. Error type ${err.statusText}: ${err.error.detail}`)
      }
    })
  }

  private validateUser() {
    this.keyToolsService.getUserUID().then(uid => {
      if (!uid || uid != this.community?.author) {
        this.router.navigate([APP_ROUTES.HOME]);
      }
    })
  }

  private extractCoordinates(geom: string): [number, number] | null {
    let match = geom.match(/POINT\(([-\d.]+) ([-\d.]+)\)/);
    if (!match)
      match = geom.match(/POINT \(([-\d.]+) ([-\d.]+)\)/);
    return match ? [parseFloat(match[2]), parseFloat(match[1])] : null;
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

  public returnToCommunity() {
    this.router.navigate([`/${APP_ROUTES.COMMUNITY}/${this.communityID}`]);
  }

  public updateContext(context: any) {
    this.loadingCreate = true;
    this.buildingInfo = context;
    this.postIntermidateBaselineData();
  }

  public generateFormArray(context: any) {
    this.buildingsArray = {
      advanced: true,
      buildings: []
    }

    context.forEach((cont: any) => {
      this.buildingsArray.buildings.push({
        buildingId: null,
        buildingName: null,
        buildingEditingName: null,
        buildingType: cont.building.building_use_id,
        comunnityProfile: cont.building.common_profile_id,
        buildingYear: this.intermediateBaselineService.transformYearToId(cont.building.construction_year),
        dwellings: cont.building.subdivision_community,
        occupants: cont.building.occupants,
        members: cont.building.subdivision_total,
      })

    });
  }

  public goBack() {
    this.editmode = true;
  }

  public postIntermidateBaselineData() {

    const lat = this.marker.getLatLng().lat;
    const lng = this.marker.getLatLng().lng;

    const data = this.buildingInfo.buildings.map((building: any) => {
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
        this.coords = [lng, lat];
        if (this.community?.name) {
          this.newCommunityName = this.changeNameNumberUpdate(this.community?.name);
        }
        this.baselineData = data;
        this.editmode = false;
        this.loadingCreate = false;
      }, error: (err: any) => {
        console.error(err)
        this.goBack();
        this.loadingCreate = false;
        this.alertsService.error(`An error occurred while creating the community. Error type ${err.statusText}: ${err.error.detail}`)
      }
    });
  }

  public saveCommunity(baselineData: any) {
    this.loadingSaveCommunity = true;
    this.basicBaselineService.postSaveCommunity(baselineData.baseline).subscribe({
      next: (data: any) => {
        this.loadingSaveCommunity = false;
        this.router.navigate([`/${APP_ROUTES.COMMUNITY}/${data.id}`]);
      }, error: (err: any) => {
        this.loadingSaveCommunity = false;
        console.error(err.message);
        this.alertsService.error(err.error.detail);
      }
    });
  }

  private changeNameNumberUpdate(name: string): string {
    const regex = /\d{2}$/;
    const match = name.match(regex);

    if (match) {

      let number = parseInt(match[0], 10) + 1;
      let newNumber = number.toString().padStart(2, '0');

      return name.replace(regex, newNumber);
    } else {
      return name;
    }
  }


}
