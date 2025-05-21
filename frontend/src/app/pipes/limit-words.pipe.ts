import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'limitWords'
})
export class LimitWordsPipe implements PipeTransform {

  transform(value: string, maxWords: number = 25): string {
    if (!value) {
      return '';
    }

    const words = value.split(/\s+/); 
    if (words.length > maxWords) {
      return words.slice(0, maxWords).join(' ') + '...';
    } else {
      return value;
    }
  }

}