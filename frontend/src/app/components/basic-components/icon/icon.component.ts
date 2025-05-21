import { HttpClient } from '@angular/common/http';
import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { SafeHtml, DomSanitizer } from '@angular/platform-browser';

@Component({
  selector: 'iconitups',
  templateUrl: './icon.component.html',
  styleUrls: ['./icon.component.scss']
})
export class IconComponent implements OnInit, OnChanges {
  @Input() iconName!: string;
  @Input() color: string = 'black';
  @Input() width: string = '20px';
  @Input() height: string = '20px';;

  public svgHtml!: SafeHtml;

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) { }

  ngOnInit(): void {
    this.loadSvg();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['iconName'] || changes['fillColor'] || changes['width'] || changes['height']) {
      this.loadSvg();
    }
  }

  // loadSvg() {
  //   const url = `./assets/icons/${this.iconName}.svg`;
  //   this.http.get(url, { responseType: 'text' }).subscribe(svg => {
  //     let updatedSvg = svg.replace(/stroke=".*?"/g, `stroke="${this.color}"`).replace(/width=".*?"/g, `width="${this.width}"`).replace(/height=".*?"/g, `height="${this.height}"`);
  //     this.svgHtml = this.sanitizer.bypassSecurityTrustHtml(updatedSvg);
  //   });
  // }

  public loadSvg() {
    const url = `assets/icons/${this.iconName}.svg`;
    this.http.get(url, { responseType: 'text' }).subscribe(svg => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(svg, 'image/svg+xml');

      const pathElement = doc.querySelector('path');
      if (pathElement) {
        pathElement.setAttribute('stroke', this.color);
      }

      const svgElement = doc.querySelector('svg');
      if (svgElement) {
        svgElement.setAttribute('width', this.width);
        svgElement.setAttribute('height', this.height);
      }

      const serializer = new XMLSerializer();
      const updatedSvg = serializer.serializeToString(doc);

      this.svgHtml = this.sanitizer.bypassSecurityTrustHtml(updatedSvg);
    });
  }

}
