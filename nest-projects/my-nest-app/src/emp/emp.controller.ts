import { Controller, Get, Post, Put, Delete, Param, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { EmpService } from './emp.service';
import { Emp } from './emp.schema';

@Controller('emp')
export class EmpController {
  constructor(private readonly empService: EmpService) {}

  @Get()
  async getAll(): Promise<Emp[]> {
    return this.empService.findAll();
  }

  @Get(':id')
  async getOne(@Param('id') id: string): Promise<Emp> {
    return this.empService.findOne(id);
  }

  @Post()
  async create(@Body() empData: Partial<Emp>): Promise<Emp> {
    return this.empService.create(empData);
  }

  @Put(':id')
  async update(@Param('id') id: string, @Body() empData: Partial<Emp>): Promise<Emp> {
    return this.empService.update(id, empData);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async delete(@Param('id') id: string): Promise<void> {
    return this.empService.delete(id);
  }
}
