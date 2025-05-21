import { ViewportScroller } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { OverpassService } from '../../../services/overpass.service';
import { MapStyleService } from '../../../services/map-style.service';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-building-selector',
  templateUrl: './building-selector.component.html',
  styleUrls: ['./building-selector.component.scss']
})
export class BuildingSelectorComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Output() exitAdvanced = new EventEmitter();
  @Input() title: string = "";
  @Input() subtitle?: string;
  @Input() title2: string = "";
  @Input() subtitle2?: string;
  @Input() numberInfo?: string;
  @Input() showMoreInfo?: string;
  @Input() onlyAdvanced: boolean = false;
  @Input() advanced: boolean = false;
  @Input() openModal: boolean = false;
  @Input() openEditNameMode: boolean = false;
  @Input() numBuildings: number = 7;
  @Input() buildings: any;
  @Input() selectedBUildings: any = [];
  @Input() buildingUseList: any;
  @Input() commonProfileList: any;
  @Input() markerMapPosition: any;

  loading: boolean = false;

  private defaultChip = 2;
  private defaultCard = 2;

  public selectedBuilding = 0;
  public selectedChip = this.defaultChip;
  public selectedCard = this.defaultCard;
  public changingLeft: boolean = false;
  public changingRight: boolean = false;

  public buildingsName = [];
  form: FormGroup = new FormGroup({});

  public readonly OFFICE_ID: number = 4;
  public readonly ADULTS_ID: number = 2;

  public validAdvancedForm: boolean = false;

  public arrayNummerOfBuildings: any = [];

  constructor(
    private formBuilder: FormBuilder,
    private viewportScroller: ViewportScroller,
  ) { }

  ngOnInit() {
    this.setForm();
    if (!this.selectedBUildings) {
      this.selectedBUildings = new Array(this.numBuildings);
      this.arrayNummerOfBuildings = new Array(this.numBuildings);
    } else {
      this.arrayNummerOfBuildings = new Array(this.selectedBUildings.length)
      if (this.buildings?.advanced === true) {
        if (!this.onlyAdvanced) {
          this.form.controls['switch'].setValue(true);
          // this.openAdvancedMode();
        }
       
      } else {
        this.loadRegularForm(this.buildings)
      }
    }
  }

  public openAdvancedMode() {

    if (!this.onlyAdvanced) {
      this.openModal = false;
      if (this.advanced === false) {
        if (!this.selectedBUildings) {
          this.selectedBUildings = new Array(this.numBuildings);
          this.arrayNummerOfBuildings = new Array(this.numBuildings);
        }
      }

      this.advanced = !this.advanced;
    } else {
      this.exitAdvanced.emit();
    }
  }

  //#region form

  public setForm() {
    this.form = this.formBuilder.group({
      buildingType: [this.defaultCard, Validators.required],
      comunnityProfile: [this.defaultChip, Validators.required],
      switch: [(this.onlyAdvanced ? true : (this.advanced ?? false)), Validators.required]

    });

    this.form.controls['switch'].valueChanges.subscribe((value: boolean) => this.openAdvancedMode());
  }

  private loadRegularForm(info: any) {
    this.advanced = info.advanced;
    this.form.controls["comunnityProfile"].setValue(info?.profile);
    this.form.controls["buildingType"].setValue(info?.type);
    this.selectedCard = info?.type;
    this.selectedChip = info?.profile;
  }

  //#endregion



  //#region cards selection

  public selectACard(card: number) {

    if (card === this.OFFICE_ID) {
      this.form.controls["comunnityProfile"].setValue(this.ADULTS_ID);
      this.selectedChip = this.ADULTS_ID;
    }

    this.form.controls["buildingType"].setValue(card);
    this.selectedCard = card;
  }

  public selectComunnity(type: number) {
    this.form.controls["comunnityProfile"].setValue(type);
    this.selectedChip = type;

  }

  //#endregion



  //#region steps configuration

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    const community = this.getCommunityInfo();
    this.next.emit(community);
  }

  private getCommunityInfo() {
    let comunnity;

    if(this.advanced){
      comunnity = {
        advanced: true,
        buildings: this.selectedBUildings,
      }
    }else{
      comunnity = {
        advanced: false,
        type: this.form.controls["buildingType"].value,
        profile: this.form.controls["comunnityProfile"].value,
      }
    }

    return comunnity
  }

  public showAlert() {
    this.openModal = true;
  }
  //#endregion

  //#region save advanced

  public saveAdvancedModel(form: any, index: number) {
    this.selectedBUildings[index] = form;
    this.validateAllForms();
  }


  public validateAllForms() {
    let validate = true;

    for (let index = 0; index < this.selectedBUildings.length; index++) {
      if (!this.selectedBUildings[index]) {
        validate = false;
      } else {
        const value = this.validate(this.selectedBUildings[index]);
        if (!value) {
          validate = false;
        }
      }

      if (this.selectedBUildings.length === (index + 1)) {
        this.validAdvancedForm = validate;
      }
    }
  }

  validate(form: any): boolean {
    if (!form.buildingId)
      return false
    if (!form.buildingName)
      return false
    if (!form.buildingType || form.buildingType < 0)
      return false
    if (!form.buildingYear || form.buildingYear < 0)
      return false
    if (!form.comunnityProfile || form.comunnityProfile < 0)
      return false
    if (!form.dwellings || form.dwellings < 0)
      return false
    if (!form.members || form.members < 0)
      return false
    if (!form.occupants || form.occupants < 0)
      return false

    return true
  }

  //#endregion

  //#region Add y delete buildings

  public addNewBuilding() {
    if (this.arrayNummerOfBuildings.length < 50) {
      this.arrayNummerOfBuildings.push(0);
      this.selectedBUildings.push(null);
      this.validateAllForms();
    }
  }

  public deleteBuilding(index: number) {
    if (this.arrayNummerOfBuildings.length > 2) {
      index = index++;
      this.arrayNummerOfBuildings.splice(index, 1);
      this.selectedBUildings.splice(index, 1);
    }

  }
  //#endregion

  //#region save name

  public saveName(name:string, index:number){
    if(name){
      index = index++;
      if(this.arrayNummerOfBuildings && this.arrayNummerOfBuildings[index] && this.arrayNummerOfBuildings[index]?.buildingName){
        this.arrayNummerOfBuildings[index].buildingName = name;
      }
    }
  }

  //#endregion

}