package com.cropdisease.backend.controller;

import com.cropdisease.backend.model.User;
import com.cropdisease.backend.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin("*")
public class AuthController {

    @Autowired
    private UserRepository userRepository;

    @PostMapping("/register")
    public String register(@RequestBody User user) {

        if(userRepository.findByEmail(user.getEmail()).isPresent()) {
            return "Email already exists";
        }

        user.setRole("FARMER");

        userRepository.save(user);

        return "User registered successfully";
    }

}
