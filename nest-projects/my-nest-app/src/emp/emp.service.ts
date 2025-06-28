import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Emp, EmpDocument } from './emp.schema';

@Injectable()
export class EmpService {
  constructor(@InjectModel(Emp.name) private empModel: Model<EmpDocument>) {}

  async findAll(): Promise<Emp[]> {
    return this.empModel.find().exec();
  }

  async findOne(id: string): Promise<Emp> {
    const emp = await this.empModel.findById(id).exec();
    if (!emp) throw new NotFoundException(`Employee ${id} not found`);
    return emp;
  }

  async create(empData: Partial<Emp>): Promise<Emp> {
    const createdEmp = new this.empModel(empData);
    return createdEmp.save();
  }

  async update(id: string, empData: Partial<Emp>): Promise<Emp> {
    const updatedEmp = await this.empModel.findByIdAndUpdate(id, empData, { new: true }).exec();
    if (!updatedEmp) throw new NotFoundException(`Employee ${id} not found`);
    return updatedEmp;
  }

  async delete(id: string): Promise<void> {
    const deleted = await this.empModel.findByIdAndDelete(id).exec();
    if (!deleted) throw new NotFoundException(`Employee ${id} not found`);
  }
}
