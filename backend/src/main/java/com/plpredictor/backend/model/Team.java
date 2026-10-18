package com.plpredictor.backend.model;

import jakarta.persistence.*;

@Entity
@Table(name = "teams")
public class Team {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    private String name;

    public Integer getId() { 
        return id;
    }
    public String getName() { 
        return name; 
    }
}