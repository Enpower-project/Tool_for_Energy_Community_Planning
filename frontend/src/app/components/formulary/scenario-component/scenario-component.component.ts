import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { AlternativeAction, AlternativesActionsArray, CardInfo, cardArrayModule } from '../../../data/types';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-scenario-component',
  templateUrl: './scenario-component.component.html',
  styleUrls: ['./scenario-component.component.scss']
})
export class ScenarioComponentComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() next = new EventEmitter();
  @Output() close = new EventEmitter();
  @Input() selectedCard: CardInfo = cardArrayModule[0];
  @Input() recommendedSelected: any;
  @Input() AlternativesList = [] as any;
  @Input() openCompare: boolean = false;

  form: FormGroup = new FormGroup({});
  public alternativas: AlternativeAction[] = [];
  public actionsList: AlternativeAction[] = AlternativesActionsArray;

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
    this.alternativas = AlternativesActionsArray.filter(alter => Object.values(this.AlternativesList).some((call: any) => call.id === alter.id));
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      reductionDemand: [{ value: this.recommendedSelected?.reductionDemand ?? null, disabled: true }, Validators.required],
      demandResponse: [{ value: this.recommendedSelected?.demandResponse ?? null, disabled: true }, Validators.required],
      solarFleet: [{ value: this.recommendedSelected?.solarFleet ?? null, disabled: true }, Validators.required],
      WindOffshoreFleet: [{ value: this.recommendedSelected?.WindOffshoreFleet ?? null, disabled: true }, Validators.required],
      HydroFleet: [{ value: this.recommendedSelected?.HydroFleet ?? null, disabled: true }, Validators.required],
      GeothermalFleet: [{ value: this.recommendedSelected?.GeothermalFleet ?? null, disabled: true }, Validators.required],
      SolarThermal: [{ value: this.recommendedSelected?.SolarThermal ?? null, disabled: true }, Validators.required],
      BiomassBoiler: [{ value: this.recommendedSelected?.BiomassBoiler ?? null, disabled: true }, Validators.required],
      GasBoiler: [{ value: this.recommendedSelected?.GasBoiler ?? null, disabled: true }, Validators.required],
      HeatPump: [{ value: this.recommendedSelected?.HeatPump ?? null, disabled: true }, Validators.required],
      GeothermalHeat: [{ value: this.recommendedSelected?.GeothermalHeat ?? null, disabled: true }, Validators.required],
      Methanisation: [{ value: this.recommendedSelected?.Methanisation ?? null, disabled: true }, Validators.required],
      CHPCombinedHeatandPower: [{ value: this.recommendedSelected?.CHPCombinedHeatandPower ?? null, disabled: true }, Validators.required],
      GasCHPCombinedHeatandPower: [{ value: this.recommendedSelected?.GasCHPCombinedHeatandPower ?? null, disabled: true }, Validators.required],
      BiomassCHPCombinedHeatandPower: [{ value: this.recommendedSelected?.BiomassCHPCombinedHeatandPower ?? null, disabled: true }, Validators.required],
      BatteryStorage: [{ value: this.recommendedSelected?.BatteryStorage ?? null, disabled: true }, Validators.required],
      HeatStorage: [{ value: this.recommendedSelected?.HeatStorage ?? null, disabled: true }, Validators.required],
      GasStorage: [{ value: this.recommendedSelected?.GasStorage ?? null, disabled: true }, Validators.required],
      CreationofDHN: [{ value: this.recommendedSelected?.CreationofDHN ?? null, disabled: true }, Validators.required],
      ConnectiontotheDHN: [{ value: this.recommendedSelected?.ConnectiontotheDHN ?? null, disabled: true }, Validators.required],
      DHNSupplier: [{ value: this.recommendedSelected?.DHNSupplier ?? null, disabled: true }, Validators.required],
      ChargingStation: [{ value: this.recommendedSelected?.ChargingStation ?? null, disabled: true }, Validators.required],
      ElectricMobility: [{ value: this.recommendedSelected?.ElectricMobility ?? null, disabled: true }, Validators.required],
      Electrification: [{ value: this.recommendedSelected?.Electrification ?? null, disabled: true }, Validators.required],
      EnergyResilience: [{ value: this.recommendedSelected?.EnergyResilience ?? null, disabled: true }, Validators.required],

      Grid: [{ value: this.recommendedSelected?.Grid ?? null, disabled: true }, Validators.required],
      DC: [{ value: this.recommendedSelected?.DC ?? null, disabled: true }, Validators.required],
      Other: [{ value: this.recommendedSelected?.Other ?? null, disabled: true }, Validators.required],
      OilBoiler: [{ value: this.recommendedSelected?.OilBoiler ?? null, disabled: true }, Validators.required],
      Hydrogen: [{ value: this.recommendedSelected?.Hydrogen ?? null, disabled: true }, Validators.required],

    });
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public createNewAlternative() {
    this.next.emit();
  }

  public openCompareOption(){
    this.openCompare = true;
  }
}
