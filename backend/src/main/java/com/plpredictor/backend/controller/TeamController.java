package com.plpredictor.backend.controller;

import com.plpredictor.backend.model.Team;
import com.plpredictor.backend.model.TeamRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class TeamController {

    private final TeamRepository teams;

    public TeamController(TeamRepository teams) {
        this.teams = teams;
    }

    @GetMapping("/teams")
    public List<Team> getTeams() {
        return teams.findAll();
    }
}