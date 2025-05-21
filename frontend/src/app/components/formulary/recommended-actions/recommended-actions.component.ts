import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { AlternativeAction, AlternativesActionsArray, CardInfo, cardArrayModule } from '../../../data/types';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-recommended-actions',
  templateUrl: './recommended-actions.component.html',
  styleUrls: ['./recommended-actions.component.scss']
})
export class RecommendedActionsComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Input() AlternativesList = [] as any;
  @Input() imgSrc: string = "./assets/images/sharing-information_nobg.png";
  @Input() selectedCard: CardInfo = cardArrayModule[0];
  @Input() recommendedSelected: any;
  @Input() openCardScenario: boolean = false;

  public alternativas: AlternativeAction[] = [];
  cardArrayModule: CardInfo[] = cardArrayModule

  public actionsList: AlternativeAction[] = AlternativesActionsArray;

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
    this.alternativas = AlternativesActionsArray.filter(alter => Object.values(this.AlternativesList).some((call: any) => call.id === alter.id));
    this.setForm();
    this.setDefaultTrue();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      reductionDemand: [this.recommendedSelected?.reductionDemand ?? null, Validators.required],
      demandResponse: [this.recommendedSelected?.demandResponse ?? null, Validators.required],
      solarFleet: [this.recommendedSelected?.solarFleet ?? null, Validators.required],
      WindOffshoreFleet: [this.recommendedSelected?.WindOffshoreFleet ?? null, Validators.required],
      HydroFleet: [this.recommendedSelected?.HydroFleet ?? null, Validators.required],
      GeothermalFleet: [this.recommendedSelected?.GeothermalFleet ?? null, Validators.required],
      SolarThermal: [this.recommendedSelected?.SolarThermal ?? null, Validators.required],
      BiomassBoiler: [this.recommendedSelected?.BiomassBoiler ?? null, Validators.required],
      GasBoiler: [this.recommendedSelected?.GasBoiler ?? null, Validators.required],
      HeatPump: [this.recommendedSelected?.HeatPump ?? null, Validators.required],
      GeothermalHeat: [this.recommendedSelected?.GeothermalHeat ?? null, Validators.required],
      Methanisation: [this.recommendedSelected?.Methanisation ?? null, Validators.required],
      CHPCombinedHeatandPower: [this.recommendedSelected?.CHPCombinedHeatandPower ?? null, Validators.required],
      GasCHPCombinedHeatandPower: [this.recommendedSelected?.GasCHPCombinedHeatandPower ?? null, Validators.required],
      BiomassCHPCombinedHeatandPower: [this.recommendedSelected?.BiomassCHPCombinedHeatandPower ?? null, Validators.required],
      BatteryStorage: [this.recommendedSelected?.BatteryStorage ?? null, Validators.required],
      HeatStorage: [this.recommendedSelected?.HeatStorage ?? null, Validators.required],
      GasStorage: [this.recommendedSelected?.GasStorage ?? null, Validators.required],
      CreationofDHN: [this.recommendedSelected?.CreationofDHN ?? null, Validators.required],
      ConnectiontotheDHN: [this.recommendedSelected?.ConnectiontotheDHN ?? null, Validators.required],
      DHNSupplier: [this.recommendedSelected?.DHNSupplier ?? null, Validators.required],
      ChargingStation: [this.recommendedSelected?.ChargingStation ?? null, Validators.required],
      ElectricMobility: [this.recommendedSelected?.ElectricMobility ?? null, Validators.required],
      Electrification: [this.recommendedSelected?.Electrification ?? null, Validators.required],
      EnergyResilience: [this.recommendedSelected?.EnergyResilience ?? null, Validators.required],

      Grid: [this.recommendedSelected?.Grid ?? null, Validators.required],
      DC: [this.recommendedSelected?.DC ?? null, Validators.required],
      Other: [this.recommendedSelected?.Other ?? null, Validators.required],
      OilBoiler: [this.recommendedSelected?.OilBoiler ?? null, Validators.required],
      Hydrogen: [this.recommendedSelected?.Hydrogen ?? null, Validators.required],
    });
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  private setDefaultTrue() {
    this.alternativas.forEach(alter => {
      this.form.controls[alter.controlName].setValue(true);
    });
  }

  public goNext() {

    if(this.checkIfAnyTrue()){


    this.recommendedSelected = {
      reductionDemand: this.form.controls["reductionDemand"].value,
      demandResponse: this.form.controls["demandResponse"].value,
      solarFleet: this.form.controls["solarFleet"].value,
      WindOffshoreFleet: this.form.controls["WindOffshoreFleet"].value,
      HydroFleet: this.form.controls["HydroFleet"].value,
      GeothermalFleet: this.form.controls["GeothermalFleet"].value,
      SolarThermal: this.form.controls["SolarThermal"].value,
      BiomassBoiler: this.form.controls["BiomassBoiler"].value,
      GasBoiler: this.form.controls["GasBoiler"].value,
      HeatPump: this.form.controls["HeatPump"].value,
      GeothermalHeat: this.form.controls["GeothermalHeat"].value,
      Methanisation: this.form.controls["Methanisation"].value,
      CHPCombinedHeatandPower: this.form.controls["CHPCombinedHeatandPower"].value,
      GasCHPCombinedHeatandPower: this.form.controls["GasCHPCombinedHeatandPower"].value,
      BiomassCHPCombinedHeatandPower: this.form.controls["BiomassCHPCombinedHeatandPower"].value,
      BatteryStorage: this.form.controls["BatteryStorage"].value,
      HeatStorage: this.form.controls["HeatStorage"].value,
      GasStorage: this.form.controls["GasStorage"].value,
      CreationofDHN: this.form.controls["CreationofDHN"].value,
      ConnectiontotheDHN: this.form.controls["ConnectiontotheDHN"].value,
      DHNSupplier: this.form.controls["DHNSupplier"].value,
      ChargingStation: this.form.controls["ChargingStation"].value,
      ElectricMobility: this.form.controls["ElectricMobility"].value,
      Electrification: this.form.controls["Electrification"].value,
      EnergyResilience: this.form.controls["EnergyResilience"].value,

      Grid: this.form.controls["Grid"].value,
      DC: this.form.controls["DC"].value,
      Other: this.form.controls["Other"].value,
      OilBoiler: this.form.controls["OilBoiler"].value,
      Hydrogen: this.form.controls["Hydrogen"].value,
    }

    this.next.emit(this.recommendedSelected);
  }

  }

  public checkIfAnyTrue(): boolean {
    const controls = this.form.controls;
    for (const controlName in controls) {
      if (controls[controlName].value === true) {
        return true;
      }
    }
    return false;
  }

}
