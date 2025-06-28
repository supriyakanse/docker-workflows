// src/emp/emp.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type EmpDocument = Emp & Document;

@Schema()
export class Emp {
  @Prop({ required: true })
  name: string;

  @Prop()
  position: string;

  @Prop()
  salary: number;
}

export const EmpSchema = SchemaFactory.createForClass(Emp);
