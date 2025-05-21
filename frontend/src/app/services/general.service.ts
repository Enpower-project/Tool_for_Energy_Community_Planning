import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Injectable({
  providedIn: 'root'
})
export class GeneralService {

  constructor(
    private translate: TranslateService,
  ) { }


  public convertEnergy(value: number, decimals: number = 2) {
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

  public convertWeight(value: number, decimals: number = 2) {
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

  public convertMoney(value: number, decimals: number = 2) {
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

  public sum(value: number[]) {
    return value.reduce((acumulador: number, valorActual: number) => {
      return acumulador + valorActual;
    }, 0)
  }

  public compareValues(value1: number, value2: number) {
    if (value1 > value2) {
      return this.translate.instant('KPI.HIGHER')
    } else if (value1 < value2) {
      return this.translate.instant('KPI.LOWER')
    }
    else {
      return this.translate.instant('KPI.EQUAL')
    }
  }

  public round2Decimals(value: number): number {
    return Math.round(value * 100) / 100;
  }

  public getRandomNumer() {
    return Math.floor(Math.random() * (1000 - 500 + 1)) + 500;
  }

  public agruparArrayPorAño(values: number[]): number[] {
    const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    const hoursPerDay = 24;
    const totalHoursInYear = 8760; //horas en un año

    if (values.length !== totalHoursInYear) {
      throw new Error("El tamaño del array no coincide con el número total de horas del año.");
    }

    let currentIndex = 0;

    return daysInMonth.map(days => {
      const chunkSize = days * hoursPerDay;
      const chunk = values.slice(currentIndex, currentIndex + chunkSize);
      currentIndex += chunkSize;
      return this.round2Decimals(this.sum(chunk));
    });
  }

}
