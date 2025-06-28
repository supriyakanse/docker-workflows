// user.controller.ts
import { Controller, Get, Post, Delete, Param, Body, ParseIntPipe, HttpCode, HttpStatus } from '@nestjs/common';
import { UserService } from './user.service';
import { User } from './user.entity';

@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}

  // GET /user
  @Get()
  async getAllUsers(): Promise<User[]> {
    return this.userService.findAll();
  }

  // GET /user/:id
  @Get(':id')
  async getUserById(@Param('id', ParseIntPipe) id: number): Promise<User> {
    return this.userService.findOne(id);
  }

  // POST /user
  @Post()
  async createUser(@Body('name') name: string): Promise<User> {
    return this.userService.create(name);
  }

  // DELETE /user/:id
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async deleteUser(@Param('id', ParseIntPipe) id: number): Promise<void> {
    return this.userService.delete(id);
  }
}
