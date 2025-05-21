import { Directive, HostListener } from '@angular/core';

@Directive({
  selector: '[PreventContextMenu]'
})
export class PreventContextMenuDirective {

  @HostListener('contextmenu', ['$event'])
  onRightClick(event: MouseEvent): void {
    event.preventDefault();
  }

  @HostListener('dragstart', ['$event'])
  onDragStart(event: DragEvent): void {
    event.preventDefault();
  }
}
